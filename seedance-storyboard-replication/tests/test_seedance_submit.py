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
    build_failure_report,
    classify_failure,
    parse_task_id,
    poll_task,
    request_sha256,
    require_approved_request,
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
    def test_request_sha256_is_stable_for_equivalent_payloads(self) -> None:
        first = {
            "model": "seedance2.0-fast-md",
            "prompt": "完整提示词",
            "duration": 10,
            "images": ["https://cos.example/storyboard.png"],
        }
        reordered = {
            "images": ["https://cos.example/storyboard.png"],
            "duration": 10,
            "prompt": "完整提示词",
            "model": "seedance2.0-fast-md",
        }

        self.assertEqual(request_sha256(first), request_sha256(reordered))

    def test_requires_matching_approval_for_exact_request(self) -> None:
        payload = {
            "model": "seedance2.0-fast-md",
            "prompt": "用户已经确认的完整提示词",
            "duration": 10,
            "ratio": "9:16",
        }
        approved = request_sha256(payload)

        require_approved_request(payload, approved)

        changed = dict(payload, prompt="确认后被修改的提示词")
        with self.assertRaisesRegex(PayloadError, "changed since user approval"):
            require_approved_request(changed, approved)

    def test_rejects_new_paid_request_without_explicit_approval(self) -> None:
        with self.assertRaisesRegex(PayloadError, "explicit user approval"):
            require_approved_request({"prompt": "not approved"}, None)

    def test_builds_fast_md_image_payload(self) -> None:
        payload = build_payload(
            prompt="按故事板生成带口播和真实动作音效的视频，不要背景音乐。",
            duration=15,
            ratio="9:16",
            image_urls=["https://cos.example/storyboard.png", "https://cos.example/product.jpg"],
            reference_video_urls=[],
        )

        self.assertEqual(payload["model"], "seedance2.0-fast-md")
        self.assertNotIn("resolution", payload)
        self.assertNotIn("reference_audios", payload)
        self.assertNotIn("reference_videos", payload)

    def test_rejects_reference_video_urls_for_fixed_b_route(self) -> None:
        with self.assertRaisesRegex(PayloadError, "reference_videos is disabled"):
            build_payload(
                prompt="Use the approved storyboard and complete script.",
                duration=10,
                ratio="9:16",
                image_urls=["https://cos.example/storyboard.png"],
                reference_video_urls=["https://cos.example/reference.mp4"],
            )

    def test_omits_optional_media_fields_when_empty(self) -> None:
        payload = build_payload(
            prompt="Generate from the complete script.",
            duration=10,
            ratio="9:16",
            image_urls=[],
            reference_video_urls=[],
        )

        self.assertNotIn("images", payload)
        self.assertNotIn("reference_videos", payload)

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
            build_payload("prompt", 10, "9:16", ["http://x/storyboard.png"], [])

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

    def test_preserves_nested_provider_error_message_for_classification(self) -> None:
        transport = FakeTransport(
            [
                (
                    400,
                    {
                        "error": {
                            "message": (
                                "[SY_ERR:10] invalid image_urls[1]: s3 upload failed: "
                                "read: connection reset by peer"
                            )
                        }
                    },
                )
            ]
        )
        client = JimmyAiClient("jimmy-secret", request_json=transport, sleep=lambda _: None)

        with self.assertRaisesRegex(SeedanceApiError, "s3 upload failed") as caught:
            client.create_video({"model": "seedance2.0-fast-md"})

        self.assertEqual(classify_failure(str(caught.exception)).code, "transient_media_fetch")

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

    def test_poll_failure_reports_provider_error_message(self) -> None:
        client = JimmyAiClient(
            "jimmy-secret",
            request_json=FakeTransport(
                [
                    {
                        "code": 0,
                        "data": {
                            "status": "failed",
                            "error_message": "PROVIDER_MODERATION_ERROR",
                        },
                    }
                ]
            ),
            sleep=lambda _: None,
        )

        with self.assertRaisesRegex(TaskFailedError, "PROVIDER_MODERATION_ERROR"):
            poll_task(client, "task-1", timeout=60, poll_interval=1)

    def test_classifies_trademark_moderation_as_storyboard_revision(self) -> None:
        diagnosis = classify_failure(
            "[SY_ERR:10] PROVIDER_MODERATION_ERROR: TRADEMARK [SY_ERR] "
            "The request failed because the output video may contain sensitive information."
        )

        self.assertEqual(diagnosis.code, "trademark_moderation")
        self.assertFalse(diagnosis.retry_allowed)
        self.assertTrue(diagnosis.requires_user_confirmation)
        self.assertTrue(diagnosis.prompt_or_image_change_required)
        self.assertIn("故事板", diagnosis.next_action)

    def test_generic_provider_moderation_does_not_infer_trademark(self) -> None:
        diagnosis = classify_failure("[SY_ERR:10] PROVIDER_MODERATION_ERROR")

        self.assertEqual(diagnosis.code, "provider_moderation_unspecified")
        self.assertNotIn("商标", diagnosis.user_message)
        self.assertTrue(diagnosis.prompt_or_image_change_required)
        self.assertFalse(diagnosis.retry_allowed)

    def test_classifies_media_fetch_timeout_as_confirmed_same_request_retry(self) -> None:
        diagnosis = classify_failure(
            "[SY_ERR:10] Read timed out [SY_ERR:10] upstream returned error "
            'invalid image_urls[1]: s3 upload failed: read: connection reset by peer'
        )

        self.assertEqual(diagnosis.code, "transient_media_fetch")
        self.assertTrue(diagnosis.retry_allowed)
        self.assertTrue(diagnosis.requires_user_confirmation)
        self.assertFalse(diagnosis.prompt_or_image_change_required)
        self.assertIn("原请求", diagnosis.next_action)

    def test_classifies_long_reference_video_as_stale_fixed_b_request(self) -> None:
        diagnosis = classify_failure(
            "invalid video_reference[0]: wait for staged video asset failed: "
            "uploaded media failed: DURATION_TOO_LONG"
        )

        self.assertEqual(diagnosis.code, "stale_reference_video")
        self.assertFalse(diagnosis.retry_allowed)
        self.assertIn("reference_videos", diagnosis.next_action)
        self.assertIn("15", diagnosis.next_action)

    def test_unknown_provider_failure_is_preserved_without_automatic_retry(self) -> None:
        raw_error = "[SY_ERR:10] an undocumented provider failure"

        report = build_failure_report(raw_error)

        self.assertEqual(report["raw_error"], raw_error)
        self.assertEqual(report["code"], "unknown_provider_failure")
        self.assertFalse(report["retry_allowed"])

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
