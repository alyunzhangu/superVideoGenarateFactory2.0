from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from config import DEFAULT_ENV_FILE, load_settings


class CosPublishError(RuntimeError):
    pass


class CosPublisher:
    def __init__(
        self,
        bucket: str,
        public_base_url: str,
        object_prefix: str,
        client: Any,
    ) -> None:
        self.bucket = bucket.strip()
        self.public_base_url = public_base_url.strip().rstrip("/")
        self.object_prefix = object_prefix.strip("/")
        self.client = client
        if not self.public_base_url.startswith("https://"):
            raise CosPublishError("COS public base URL must use https://")

    @classmethod
    def from_settings(cls, settings: Any, run_id: str) -> "CosPublisher":
        try:
            settings.require_cos()
        except Exception as exc:
            raise CosPublishError(str(exc)) from exc

        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError as exc:
            raise CosPublishError("Tencent COS SDK is not installed. Install cos-python-sdk-v5.") from exc

        object_prefix = settings.cos_object_prefix.strip("/")
        normalized_run_id = run_id.strip("/")
        if normalized_run_id:
            object_prefix = f"{object_prefix}/{normalized_run_id}" if object_prefix else normalized_run_id
        config = CosConfig(
            Region=settings.cos_region,
            SecretId=settings.cos_secret_id,
            SecretKey=settings.cos_secret_key,
            Scheme="https",
        )
        return cls(
            settings.cos_bucket,
            settings.cos_public_base_url,
            object_prefix,
            CosS3Client(config),
        )

    def publish(self, local_path: Path, object_key: str) -> str:
        if not local_path.is_file():
            raise CosPublishError(f"Media file not found: {local_path}")
        key = self._build_key(object_key)
        self.client.upload_file(Bucket=self.bucket, LocalFilePath=str(local_path), Key=key)
        return f"{self.public_base_url}/{quote(key, safe='/')}"

    def _build_key(self, object_key: str) -> str:
        normalized = object_key.strip("/").replace("\\", "/")
        if not normalized:
            raise CosPublishError("COS object key is required")
        if self.object_prefix:
            return f"{self.object_prefix}/{normalized}"
        return normalized


def publish_media_manifest(
    publisher: CosPublisher,
    media_paths: Iterable[Path],
    output_path: Path,
    *,
    object_dir: str = "inputs",
) -> list[dict[str, str]]:
    manifest: list[dict[str, str]] = []
    normalized_dir = object_dir.strip("/")
    for media_path in media_paths:
        path = Path(media_path)
        object_key = f"{normalized_dir}/{path.name}" if normalized_dir else path.name
        url = publisher.publish(path, object_key)
        manifest.append(
            {
                "filename": path.name,
                "local_path": str(path),
                "object_key": object_key,
                "url": url,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish local Seedance media references to public Tencent COS URLs.")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--run-id", default=_default_run_id())
    parser.add_argument("--object-dir", default="inputs")
    parser.add_argument("--output", type=Path, default=Path("published_media.json"))
    parser.add_argument("--media", type=Path, action="append", required=True)
    args = parser.parse_args()

    settings = load_settings(args.env_file)
    publisher = CosPublisher.from_settings(settings, args.run_id)
    manifest = publish_media_manifest(
        publisher,
        args.media,
        args.output,
        object_dir=args.object_dir,
    )
    for item in manifest:
        print(f"{item['filename']}\t{item['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
