from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
import math
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

    def to_dict(self) -> dict:
        return {
            "total_source_duration": self.total_source_duration,
            "retime_scale": self.retime_scale,
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


def plan_segments(boundaries: Sequence[float]) -> SegmentPlan:
    normalized = _normalize_boundaries(boundaries)
    total = normalized[-1] - normalized[0]
    if total <= 15:
        return _one_segment(normalized, total, 1.0)
    if total <= 17:
        return _one_segment(normalized, 15, 15 / total)

    segment_count = math.ceil(total / 15)
    target = total / segment_count
    candidates: list[tuple[float, list[float], list[float]]] = []
    inner_boundaries = normalized[1:-1]
    for chosen in itertools.combinations(inner_boundaries, segment_count - 1):
        points = [normalized[0], *chosen, normalized[-1]]
        durations = [right - left for left, right in zip(points, points[1:])]
        if all(5 <= duration <= 15 for duration in durations):
            score = sum((duration - target) ** 2 for duration in durations)
            candidates.append((score, points, durations))

    if not candidates:
        raise PlanningError(
            "No 5-15 second partition exists at the approved boundaries; "
            "split the Cut at an internal action beat."
        )

    _, points, durations = min(candidates, key=lambda item: item[0])
    return SegmentPlan(
        total_source_duration=total,
        retime_scale=1.0,
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
    args = parser.parse_args()

    plan = plan_segments(_load_boundaries(args.cuts_json))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
