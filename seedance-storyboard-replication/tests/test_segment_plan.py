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

    def test_uses_selected_story_boundary_for_eighteen_seconds(self) -> None:
        plan = plan_segments([0, 4, 9, 13, 18], split_boundary=9)

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 9), (9, 18)],
        )

    def test_uses_selected_story_boundary_for_twenty_seconds(self) -> None:
        plan = plan_segments([0, 5, 10, 15, 20], split_boundary=15)

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 15), (15, 20)],
        )

    def test_uses_selected_story_boundary_for_twenty_five_seconds(self) -> None:
        plan = plan_segments([0, 6, 11, 18, 25], split_boundary=11)

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 11), (11, 25)],
        )

    def test_uses_selected_story_boundary_for_twenty_seven_seconds(self) -> None:
        plan = plan_segments([0, 7, 12, 14, 21, 27], split_boundary=14)

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 14), (14, 27)],
        )

    def test_thirty_seconds_requires_the_fifteen_second_boundary(self) -> None:
        plan = plan_segments([0, 8, 15, 23, 30], split_boundary=15)

        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 15), (15, 30)],
        )

    def test_requires_a_story_selected_boundary_above_seventeen_seconds(self) -> None:
        with self.assertRaisesRegex(PlanningError, "story-selected split_boundary"):
            plan_segments([0, 6, 11, 18, 25])

    def test_rejects_split_that_is_not_an_approved_boundary(self) -> None:
        with self.assertRaisesRegex(PlanningError, "approved Cut boundary"):
            plan_segments([0, 6, 11, 18, 25], split_boundary=12)

    def test_rejects_reference_video_longer_than_thirty_seconds(self) -> None:
        with self.assertRaisesRegex(PlanningError, "at most 30 seconds"):
            plan_segments([0, 8, 15, 23, 31], split_boundary=15)

    def test_rejects_duplicate_boundaries(self) -> None:
        with self.assertRaisesRegex(PlanningError, "strictly increasing"):
            plan_segments([0, 5, 5, 10])

    def test_rejects_an_unsplittable_cut_longer_than_fifteen_seconds(self) -> None:
        with self.assertRaisesRegex(PlanningError, "story-selected split_boundary"):
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
                    "--split-boundary",
                    "9",
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
