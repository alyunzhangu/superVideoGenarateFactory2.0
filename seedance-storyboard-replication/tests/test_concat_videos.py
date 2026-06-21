from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from concat_videos import ConcatError, concat_segments, probe_media  # noqa: E402


def _require_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise unittest.SkipTest("ffmpeg and ffprobe are required")


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _make_av_segment(path: Path, color: str, frequency: int) -> None:
    _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=360x640:d=1",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration=1",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )


def _make_video_only_segment(path: Path, color: str) -> None:
    _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=360x640:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )


def _make_av_segment_with_size(path: Path, color: str, frequency: int, size: str) -> None:
    _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={size}:d=1",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration=1",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )


def _make_audio_only(path: Path) -> None:
    _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-c:a",
            "aac",
            str(path),
        ]
    )


class ConcatVideosTest(unittest.TestCase):
    def test_probe_media_reports_video_audio_and_duration(self) -> None:
        _require_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            segment = Path(tmp) / "segment-01.mp4"
            _make_av_segment(segment, "red", 440)

            media = probe_media(segment)

        self.assertTrue(media.has_video)
        self.assertTrue(media.has_audio)
        self.assertGreater(media.duration, 0.9)

    def test_probe_media_rejects_audio_only_file(self) -> None:
        _require_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "audio-only.m4a"
            _make_audio_only(audio)

            with self.assertRaisesRegex(ConcatError, "no video stream"):
                probe_media(audio)

    def test_concat_rejects_mixed_audio_presence_when_audio_expected(self) -> None:
        _require_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with_audio = tmp_path / "with-audio.mp4"
            without_audio = tmp_path / "without-audio.mp4"
            output = tmp_path / "final.mp4"
            _make_av_segment(with_audio, "red", 440)
            _make_video_only_segment(without_audio, "blue")

            with self.assertRaisesRegex(ConcatError, "without-audio.mp4"):
                concat_segments([with_audio, without_audio], output, expect_audio=True)

    def test_concatenates_two_segments_and_preserves_audio(self) -> None:
        _require_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            first = tmp_path / "segment-01.mp4"
            second = tmp_path / "segment-02.mp4"
            output = tmp_path / "final.mp4"
            _make_av_segment(first, "red", 440)
            _make_av_segment(second, "blue", 660)

            concat_segments([first, second], output, expect_audio=True)
            media = probe_media(output)

        self.assertTrue(media.has_video)
        self.assertTrue(media.has_audio)
        self.assertGreaterEqual(media.duration, 1.8)
        self.assertLessEqual(media.duration, 2.2)

    def test_normalizes_different_dimensions_before_concat(self) -> None:
        _require_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            first = tmp_path / "segment-01.mp4"
            second = tmp_path / "segment-02.mp4"
            output = tmp_path / "final.mp4"
            _make_av_segment_with_size(first, "red", 440, "360x640")
            _make_av_segment_with_size(second, "blue", 660, "320x640")

            concat_segments([first, second], output, expect_audio=True)
            media = probe_media(output)

        self.assertTrue(media.has_video)
        self.assertTrue(media.has_audio)
        self.assertEqual((media.width, media.height), (360, 640))
        self.assertGreaterEqual(media.duration, 1.8)
        self.assertLessEqual(media.duration, 2.2)


if __name__ == "__main__":
    unittest.main()
