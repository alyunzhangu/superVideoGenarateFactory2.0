from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import shlex
import subprocess
import tempfile


class ConcatError(RuntimeError):
    pass


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    has_video: bool
    has_audio: bool
    duration: float
    video_codec: str = ""
    audio_codec: str = ""
    width: int = 0
    height: int = 0


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def probe_media(path: Path) -> MediaInfo:
    if not path.is_file():
        raise ConcatError(f"Media file not found: {path}")
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    if result.returncode != 0:
        raise ConcatError(f"ffprobe failed for {path}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not video_streams:
        raise ConcatError(f"Media file has no video stream: {path}")
    video = video_streams[0]
    audio = audio_streams[0] if audio_streams else {}
    duration = data.get("format", {}).get("duration") or video.get("duration") or 0
    return MediaInfo(
        path=path,
        has_video=True,
        has_audio=bool(audio_streams),
        duration=float(duration),
        video_codec=str(video.get("codec_name") or ""),
        audio_codec=str(audio.get("codec_name") or ""),
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
    )


def concat_segments(
    segment_paths: list[Path],
    output_path: Path,
    *,
    expect_audio: bool = True,
) -> Path:
    if not segment_paths:
        raise ConcatError("At least one segment is required")
    media = [probe_media(Path(path)) for path in segment_paths]
    if expect_audio:
        missing_audio = [info.path for info in media if not info.has_audio]
        if missing_audio:
            raise ConcatError(f"Expected audio stream is missing: {missing_audio[0]}")
    audio_presence = {info.has_audio for info in media}
    if len(audio_presence) > 1:
        mixed = [info.path for info in media if not info.has_audio][0]
        raise ConcatError(f"Mixed audio presence across segments; missing audio in {mixed}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if _compatible_for_copy(media):
            list_path = _write_concat_list(tmp_path / "concat-list.txt", [info.path for info in media])
            _run_ffmpeg_concat(list_path, output_path)
        else:
            normalized = [
                _normalize_segment(
                    info.path,
                    tmp_path / f"normalized-{index:03d}.mp4",
                    width=media[0].width,
                    height=media[0].height,
                    include_audio=media[0].has_audio,
                )
                for index, info in enumerate(media, start=1)
            ]
            list_path = _write_concat_list(tmp_path / "concat-list.txt", normalized)
            _run_ffmpeg_concat(list_path, output_path)

    final_info = probe_media(output_path)
    if expect_audio and not final_info.has_audio:
        raise ConcatError(f"Final output has no audio stream: {output_path}")
    return output_path


def _compatible_for_copy(media: list[MediaInfo]) -> bool:
    first = media[0]
    return all(
        info.video_codec == first.video_codec
        and info.audio_codec == first.audio_codec
        and info.width == first.width
        and info.height == first.height
        and info.has_audio == first.has_audio
        for info in media
    )


def _write_concat_list(path: Path, segments: list[Path]) -> Path:
    lines = [f"file {shlex.quote(str(segment))}" for segment in segments]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _run_ffmpeg_concat(list_path: Path, output_path: Path) -> None:
    result = _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(output_path),
        ]
    )
    if result.returncode != 0:
        raise ConcatError(f"ffmpeg concat failed: {result.stderr.strip()}")


def _normalize_segment(
    input_path: Path,
    output_path: Path,
    *,
    width: int,
    height: int,
    include_audio: bool,
) -> Path:
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
    ]
    if include_audio:
        command.extend(["-c:a", "aac"])
    else:
        command.append("-an")
    command.append(str(output_path))
    result = _run(command)
    if result.returncode != 0:
        raise ConcatError(f"ffmpeg normalize failed for {input_path}: {result.stderr.strip()}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Concatenate Seedance video segments without dropping audio.")
    parser.add_argument("--segment", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-audio-expected", action="store_true")
    args = parser.parse_args()

    concat_segments(args.segment, args.output, expect_audio=not args.no_audio_expected)
    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
