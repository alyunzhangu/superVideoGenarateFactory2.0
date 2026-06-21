from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence


class PlanningError(ValueError):
    pass


@dataclass(frozen=True)
class Segment:
    source_start: float
    source_end: float
    output_duration: float

    @property
    def source_duration(self) -> float:
        return self.source_end - self.source_start

    def to_dict(self) -> dict[str, float]:
        return {
            "source_start": self.source_start,
            "source_end": self.source_end,
            "source_duration": self.source_duration,
            "segment_local_start": 0.0,
            "segment_local_end": self.output_duration,
            "output_duration": self.output_duration,
        }


@dataclass(frozen=True)
class SegmentPlan:
    total_source_duration: float
    retime_scale: float
    segments: tuple[Segment, ...]
    selected_split_boundary: float | None = None

    def to_dict(self) -> dict:
        return {
            "total_source_duration": self.total_source_duration,
            "retime_scale": self.retime_scale,
            "selected_split_boundary": self.selected_split_boundary,
            "segments": [segment.to_dict() for segment in self.segments],
        }


def _normalize_boundaries(boundaries: Sequence[float]) -> list[float]:
    if len(boundaries) < 2:
        raise PlanningError("At least two boundaries are required")
    normalized = [float(boundary) for boundary in boundaries]
    for left, right in zip(normalized, normalized[1:]):
        if right <= left:
            raise PlanningError("Cut boundaries must be strictly increasing")
    return normalized


def _one_segment(boundaries: list[float], output_duration: float, retime_scale: float) -> SegmentPlan:
    return SegmentPlan(
        total_source_duration=boundaries[-1] - boundaries[0],
        retime_scale=retime_scale,
        segments=(Segment(boundaries[0], boundaries[-1], output_duration),),
    )


def plan_segments(
    boundaries: Sequence[float],
    split_boundary: float | None = None,
) -> SegmentPlan:
    normalized = _normalize_boundaries(boundaries)
    total = normalized[-1] - normalized[0]
    if total > 30:
        raise PlanningError("Reference video duration must be at most 30 seconds")
    if total <= 15:
        return _one_segment(normalized, total, 1.0)
    if total <= 17:
        return _one_segment(normalized, 15, 15 / total)

    if split_boundary is None:
        raise PlanningError(
            "A story-selected split_boundary is required above 17 seconds; "
            "do not choose a boundary from duration balance alone"
        )
    selected = next(
        (
            boundary
            for boundary in normalized[1:-1]
            if abs(boundary - float(split_boundary)) <= 1e-6
        ),
        None,
    )
    if selected is None:
        raise PlanningError(
            "split_boundary must be an approved Cut boundary; revise the Cut at a "
            "natural internal action beat and ask the user to approve it"
        )
    points = [normalized[0], selected, normalized[-1]]
    durations = [right - left for left, right in zip(points, points[1:])]
    if not all(5 <= duration <= 15 for duration in durations):
        legal_start = max(normalized[0] + 5, normalized[-1] - 15)
        legal_end = min(normalized[0] + 15, normalized[-1] - 5)
        raise PlanningError(
            "story-selected split_boundary creates a segment outside 5-15 seconds; "
            f"choose an approved narrative boundary from {legal_start:g} to {legal_end:g} seconds"
        )
    return SegmentPlan(
        total_source_duration=total,
        retime_scale=1.0,
        selected_split_boundary=selected,
        segments=tuple(
            Segment(left, right, duration)
            for left, right, duration in zip(points, points[1:], durations)
        ),
    )


def _load_boundaries(cuts_json: Path) -> list[float]:
    data = json.loads(cuts_json.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [float(value) for value in data]
    if isinstance(data, dict) and isinstance(data.get("boundaries"), list):
        return [float(value) for value in data["boundaries"]]
    if isinstance(data, dict) and isinstance(data.get("cuts"), list):
        cuts = data["cuts"]
        if not cuts:
            raise PlanningError("cuts must not be empty")
        boundaries = [float(cuts[0]["start"])]
        boundaries.extend(float(cut["end"]) for cut in cuts)
        return boundaries
    raise PlanningError("cuts JSON must be a boundary list or an object with boundaries/cuts")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan 1-15 second Seedance segments from Cut boundaries.")
    parser.add_argument("--cuts-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split-boundary", type=float)
    args = parser.parse_args()

    plan = plan_segments(
        _load_boundaries(args.cuts_json),
        split_boundary=args.split_boundary,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
