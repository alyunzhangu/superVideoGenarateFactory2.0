from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Mapping


DEFAULT_ENV_FILE = Path.home() / ".codex" / "secrets" / "seedance.env"


class ConfigurationError(RuntimeError):
    pass


def _parse_env(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


@dataclass(frozen=True)
class Settings:
    jimmy_api_key: str = field(repr=False)
    jimmy_base_url: str
    cos_bucket: str
    cos_region: str
    cos_secret_id: str = field(repr=False)
    cos_secret_key: str = field(repr=False)
    cos_object_prefix: str
    cos_public_base_url: str

    def require_jimmy(self) -> None:
        if not self.jimmy_api_key:
            raise ConfigurationError("Missing configuration: JIMMYAI_API_KEY")

    def require_cos(self) -> None:
        missing = [
            name
            for name, value in (
                ("TENCENT_COS_BUCKET", self.cos_bucket),
                ("TENCENT_COS_REGION", self.cos_region),
                ("TENCENT_COS_SECRET_ID", self.cos_secret_id),
                ("TENCENT_COS_SECRET_KEY", self.cos_secret_key),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError("Missing configuration: " + ", ".join(missing))


def load_settings(
    path: Path = DEFAULT_ENV_FILE,
    *,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    file_values = _parse_env(path)
    merged = {**file_values, **dict(os.environ if environ is None else environ)}

    def value(primary: str, alias: str = "", default: str = "") -> str:
        return merged.get(primary) or (merged.get(alias) if alias else "") or default

    bucket = value("TENCENT_COS_BUCKET", "TKAGENT_COS_BUCKET")
    region = value("TENCENT_COS_REGION", "TKAGENT_COS_REGION")
    public_base = value("TENCENT_COS_PUBLIC_BASE_URL", "TKAGENT_COS_PUBLIC_BASE_URL")
    if not public_base and bucket and region:
        public_base = f"https://{bucket}.cos.{region}.myqcloud.com"

    return Settings(
        jimmy_api_key=value("JIMMYAI_API_KEY"),
        jimmy_base_url=value("JIMMYAI_BASE_URL", default="https://www.jimmyai.cn"),
        cos_bucket=bucket,
        cos_region=region,
        cos_secret_id=value("TENCENT_COS_SECRET_ID", "TKAGENT_COS_SECRET_ID"),
        cos_secret_key=value("TENCENT_COS_SECRET_KEY", "TKAGENT_COS_SECRET_KEY"),
        cos_object_prefix=value(
            "TENCENT_COS_OBJECT_PREFIX",
            "TKAGENT_COS_OBJECT_PREFIX",
            "seedance-storyboard",
        ).strip("/"),
        cos_public_base_url=public_base.rstrip("/"),
    )
