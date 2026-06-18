from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from seedance_submit import (  # noqa: E402
    JimmyAiClient,
    PayloadError,
    PollTimeoutError,
    SeedanceApiError,
    TaskFailedError,
    build_payload,
    parse_task_id,
    poll_task,
)


class FakeClock:
    def __init__(self, values: list[float]) -> None:
        self.values = values

    def __call__(self) -> float:
        if len(self.values) == 1:
            return self.values[0]
        return self.values.pop(0)


class FakeTransport:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class SeedanceSubmitTest(unittest.TestCase):
    def test_builds_fast_md_reference_payload(self) -> None:
        payload = build_payload(
            prompt="按故事板生成带口播和真实动作音效的视频，不要背景音乐。",
            duration=15,
            ratio="9:16",
            image_urls=["https://cos.example/storyboard.png", "https://cos.example/product.jpg"],
            reference_video_urls=["https://cos.example/reference.mp4"],
        )

        self.assertEqual(payload["model"], "seedance2.0-fast-md")
        self.assertNotIn("resolution", payload)
        self.assertNotIn("reference_audios", payload)
        self.assertEqual(payload["reference_videos"], ["https://cos.example/reference.mp4"])

    def test_rejects_more_than_four_images(self) -> None:
        with self.assertRaisesRegex(PayloadError, "at most 4"):
            build_payload(
                "prompt",
                10,
                "9:16",
                [f"https://x/{index}.png" for index in range(5)],
                ["https://x/ref.mp4"],
            )

    def test_rejects_non_public_https_urls(self) -> None:
        with self.assertRaisesRegex(PayloadError, "public HTTPS"):
            build_payload("prompt", 10, "9:16", ["http://x/storyboard.png"], ["https://x/ref.mp4"])

    def test_accepts_documented_success_code_variants(self) -> None:
        self.assertEqual(parse_task_id({"code": 0, "data": {"task_id": "a"}}), "a")
        self.assertEqual(parse_task_id({"code": "20000", "data": {"task_id": "b"}}), "b")

    def test_retries_transient_create_errors_and_returns_task_id(self) -> None:
        transport = FakeTransport(
            [
                (500, {"code": 500, "message": "temporary"}),
                (429, {"code": 429, "message": "busy"}),
                (200, {"code": 0, "data": {"task_id": "task-1"}}),
            ]
        )
        client = JimmyAiClient(
            api_key="jimmy-secret",
            request_json=transport,
            sleep=lambda _: None,
        )

        task_id = client.create_video({"model": "seedance2.0-fast-md"})

        self.assertEqual(task_id, "task-1")
        self.assertEqual([call["method"] for call in transport.calls], ["POST", "POST", "POST"])

    def test_rejects_unauthorized_without_retrying(self) -> None:
        transport = FakeTransport([(401, {"message": "unauthorized"})])
        client = JimmyAiClient("bad-key", request_json=transport, sleep=lambda _: None)

        with self.assertRaisesRegex(SeedanceApiError, "401"):
            client.create_video({"model": "seedance2.0-fast-md"})

        self.assertEqual(len(transport.calls), 1)

    def test_polls_until_completed_video_url(self) -> None:
        transport = FakeTransport(
            [
                {"code": 0, "data": {"status": "queued"}},
                {"code": 0, "data": {"status": "processing"}},
                {"code": 0, "data": {"status": "completed", "result": {"video_url": "https://cdn.example/result.mp4"}}},
            ]
        )
        client = JimmyAiClient("jimmy-secret", request_json=transport, sleep=lambda _: None)

        video_url = poll_task(client, "task-1", timeout=60, poll_interval=1)

        self.assertEqual(video_url, "https://cdn.example/result.mp4")
        self.assertEqual([call["method"] for call in transport.calls], ["GET", "GET", "GET"])

    def test_poll_failure_raises_task_failed_error(self) -> None:
        client = JimmyAiClient(
            "jimmy-secret",
            request_json=FakeTransport([{"code": 0, "data": {"status": "failed", "message": "bad prompt"}}]),
            sleep=lambda _: None,
        )

        with self.assertRaisesRegex(TaskFailedError, "bad prompt"):
            poll_task(client, "task-1", timeout=60, poll_interval=1)

    def test_poll_timeout_without_sleeping(self) -> None:
        client = JimmyAiClient(
            "jimmy-secret",
            request_json=FakeTransport(
                [
                    {"code": 0, "data": {"status": "queued"}},
                    {"code": 0, "data": {"status": "processing"}},
                ]
            ),
            sleep=lambda _: None,
            clock=FakeClock([0, 0, 31, 31]),
        )

        with self.assertRaisesRegex(PollTimeoutError, "timed out"):
            poll_task(client, "task-1", timeout=30, poll_interval=1)

    def test_downloads_completed_video_to_result_mp4(self) -> None:
        downloads: list[tuple[str, Path]] = []

        def download(url: str, output_path: Path) -> None:
            downloads.append((url, output_path))
            output_path.write_bytes(b"mp4")

        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "result.mp4"
            client = JimmyAiClient("jimmy-secret", download=download)
            client.download_video("https://cdn.example/result.mp4", result_path)

            self.assertEqual(result_path.read_bytes(), b"mp4")

        self.assertEqual(downloads[0][0], "https://cdn.example/result.mp4")


if __name__ == "__main__":
    unittest.main()
