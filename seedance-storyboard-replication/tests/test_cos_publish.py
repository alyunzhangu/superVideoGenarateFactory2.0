import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from cos_publish import CosPublisher, CosPublishError, publish_media_manifest  # noqa: E402


class FakeCosClient:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []

    def upload_file(self, *, Bucket: str, LocalFilePath: str, Key: str) -> None:  # noqa: N803
        self.uploads.append((Bucket, LocalFilePath, Key))


class CosPublisherTest(unittest.TestCase):
    def test_uploads_and_url_encodes_the_public_object_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "参考 video 01.mp4"
            media.write_bytes(b"video")
            client = FakeCosClient()
            publisher = CosPublisher(
                bucket="seedance-temp-1300000000",
                public_base_url="https://seedance-temp-1300000000.cos.ap-guangzhou.myqcloud.com",
                object_prefix="seedance-storyboard/run-1",
                client=client,
            )
            url = publisher.publish(media, "inputs/参考 video 01.mp4")

        self.assertEqual(client.uploads[0][2], "seedance-storyboard/run-1/inputs/参考 video 01.mp4")
        self.assertIn("%E5%8F%82%E8%80%83%20video%2001.mp4", url)

    def test_rejects_non_https_public_base_url(self) -> None:
        with self.assertRaises(CosPublishError):
            CosPublisher("bucket", "http://example.com", "prefix", FakeCosClient())

    def test_rejects_missing_media_file(self) -> None:
        publisher = CosPublisher(
            "bucket",
            "https://bucket.cos.ap-guangzhou.myqcloud.com",
            "prefix",
            FakeCosClient(),
        )

        with self.assertRaisesRegex(CosPublishError, "Media file not found"):
            publisher.publish(Path("/tmp/does-not-exist.mp4"), "inputs/missing.mp4")

    def test_writes_a_manifest_for_repeated_media_uploads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "reference.mp4"
            board = tmp_path / "storyboard.png"
            output = tmp_path / "published_media.json"
            video.write_bytes(b"video")
            board.write_bytes(b"image")
            client = FakeCosClient()
            publisher = CosPublisher(
                "bucket",
                "https://bucket.cos.ap-guangzhou.myqcloud.com",
                "seedance-storyboard/run-1",
                client,
            )

            manifest = publish_media_manifest(
                publisher,
                [video, board],
                output,
                object_dir="inputs",
            )
            written = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual([item["filename"] for item in manifest], ["reference.mp4", "storyboard.png"])
        self.assertEqual(manifest, written)
        self.assertEqual(
            [upload[2] for upload in client.uploads],
            [
                "seedance-storyboard/run-1/inputs/reference.mp4",
                "seedance-storyboard/run-1/inputs/storyboard.png",
            ],
        )
        self.assertEqual(
            [item["url"] for item in manifest],
            [
                "https://bucket.cos.ap-guangzhou.myqcloud.com/seedance-storyboard/run-1/inputs/reference.mp4",
                "https://bucket.cos.ap-guangzhou.myqcloud.com/seedance-storyboard/run-1/inputs/storyboard.png",
            ],
        )


if __name__ == "__main__":
    unittest.main()
