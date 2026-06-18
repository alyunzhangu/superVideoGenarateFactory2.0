import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from segment_plan import PlanningError, plan_segments  # noqa: E402


class SegmentPlanTest(unittest.TestCase):
    def test_keeps_fifteen_seconds_as_one_segment(self) -> None:
        plan = plan_segments([0, 5, 10, 15])

        self.assertEqual([segment.output_duration for segment in plan.segments], [15])
        self.assertEqual(plan.retime_scale, 1.0)

    def test_compresses_seventeen_seconds_to_fifteen(self) -> None:
        plan = plan_segments([0, 4, 9, 13, 17])

        self.assertEqual([segment.output_duration for segment in plan.segments], [15])
        self.assertAlmostEqual(plan.retime_scale, 15 / 17)

    def test_balances_eighteen_seconds_without_short_tail(self) -> None:
        plan = plan_segments([0, 4, 9, 13, 18])

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 9), (9, 18)],
        )

    def test_balances_twenty_seconds_as_two_ten_second_segments(self) -> None:
        plan = plan_segments([0, 5, 10, 15, 20])

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 10), (10, 20)],
        )

    def test_plans_twenty_nine_seconds_as_two_balanced_segments(self) -> None:
        plan = plan_segments([0, 7, 14, 20, 29])

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 14), (14, 29)],
        )

    def test_rejects_duplicate_boundaries(self) -> None:
        with self.assertRaisesRegex(PlanningError, "strictly increasing"):
            plan_segments([0, 5, 5, 10])

    def test_rejects_an_unsplittable_cut_longer_than_fifteen_seconds(self) -> None:
        with self.assertRaisesRegex(PlanningError, "split the Cut"):
            plan_segments([0, 18])

    def test_cli_writes_source_and_segment_local_mappings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cuts_json = tmp_path / "cuts.json"
            output_json = tmp_path / "segment_plan.json"
            cuts_json.write_text(json.dumps([0, 4, 9, 13, 18]), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "segment_plan.py"),
                    "--cuts-json",
                    str(cuts_json),
                    "--output",
                    str(output_json),
                ],
                check=True,
            )

            plan = json.loads(output_json.read_text(encoding="utf-8"))

        self.assertEqual(
            [
                (
                    segment["source_start"],
                    segment["source_end"],
                    segment["segment_local_start"],
                    segment["segment_local_end"],
                )
                for segment in plan["segments"]
            ],
            [(0.0, 9.0, 0.0, 9.0), (9.0, 18.0, 0.0, 9.0)],
        )


if __name__ == "__main__":
    unittest.main()
