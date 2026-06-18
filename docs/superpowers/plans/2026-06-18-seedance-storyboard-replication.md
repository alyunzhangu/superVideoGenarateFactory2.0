# Seedance Storyboard Replication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and install a Codex skill that turns an approved or reverse-engineered ecommerce video script into an image2 storyboard, publishes references to Tencent COS, generates `seedance2.0-fast-md` videos through JimmyAI, and joins long outputs with audio preserved.

**Architecture:** Codex owns route selection, reference-video understanding, image2 generation, prompt composition, and user approval gates. Small Python CLIs own deterministic configuration, segmentation, COS upload, JimmyAI task lifecycle, download, and FFmpeg validation/concatenation. The installed skill reads only `~/.codex/secrets/seedance.env`; network clients and subprocess runners are injected in tests.

**Tech Stack:** Codex Skills Markdown, Python 3.11+ standard library, `cos-python-sdk-v5`, `unittest`, FFmpeg/FFprobe, shell installation scripts.

---

## File Map

Create these files:

```text
.gitignore
requirements.txt
install.sh
check_install.sh
seedance-storyboard-replication/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── fukeGem.md
│   ├── daohuo_storyboard_prompt.md
│   ├── seedance-prompt.md
│   ├── jimmyai-api.md
│   └── seedance.env.example
├── scripts/
│   ├── config.py
│   ├── segment_plan.py
│   ├── cos_publish.py
│   ├── seedance_submit.py
│   └── concat_videos.py
└── tests/
    ├── test_skill_contract.py
    ├── test_config.py
    ├── test_segment_plan.py
    ├── test_cos_publish.py
    ├── test_seedance_submit.py
    └── test_concat_videos.py
```

Responsibilities:

- `SKILL.md`: route selection, approval gates, image allocation, and orchestration.
- `config.py`: load and validate the one private env file without logging secrets.
- `segment_plan.py`: turn approved Cut boundaries into 1-15 second API segments.
- `cos_publish.py`: upload local media and return anonymous public HTTPS URLs.
- `seedance_submit.py`: validate payloads, create/resume/poll tasks, and download MP4 results.
- `concat_videos.py`: inspect streams and concatenate segments without dropping audio.
- `references/*`: prompt and current API knowledge loaded only when the route needs it.
- Root scripts: install and verify the portable skill without copying secrets.

Do not modify or delete the user's root-level `storyPrompt.md`. Copy the two approved source prompts into the skill and leave their originals intact.

### Task 1: Scaffold the Skill and Establish the RED Contract

**Files:**
- Create temporarily, then move after scaffolding: `tests/test_skill_contract.py`
- Create: `seedance-storyboard-replication/tests/test_skill_contract.py`
- Create: `seedance-storyboard-replication/SKILL.md`
- Create: `seedance-storyboard-replication/agents/openai.yaml`

- [ ] **Step 1: Write the failing scaffold test**

```python
from pathlib import Path
import unittest


CONTAINER = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    CONTAINER
    if CONTAINER.name == "seedance-storyboard-replication"
    else CONTAINER / "seedance-storyboard-replication"
)


class SkillScaffoldTest(unittest.TestCase):
    def test_skill_has_discoverable_metadata_and_resource_directories(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: seedance-storyboard-replication", skill_text)
        self.assertIn("Use when", skill_text.split("---", 2)[1])
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").exists())
        self.assertTrue((SKILL_ROOT / "references").is_dir())
        self.assertTrue((SKILL_ROOT / "scripts").is_dir())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_skill_contract.py' -v
```

Expected: FAIL because the skill scaffold does not exist.

- [ ] **Step 3: Initialize the official skill scaffold**

Run:

```bash
python3 /Users/jiangyongjian/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  seedance-storyboard-replication \
  --path /Users/jiangyongjian/workspace/copyVideoSkill \
  --resources scripts,references \
  --interface display_name="Seedance Storyboard Replication" \
  --interface short_description="复刻带货短视频并通过 Seedance 生成成片" \
  --interface default_prompt="使用参考视频、分镜脚本和产品素材生成故事板与 Seedance 成片。"
mkdir -p seedance-storyboard-replication/tests
mv tests/test_skill_contract.py seedance-storyboard-replication/tests/test_skill_contract.py
rmdir tests
```

Then replace the generated frontmatter with:

```markdown
---
name: seedance-storyboard-replication
description: Use when a user wants to replicate an ecommerce short video from a reference video, an approved storyboard script, character references, or product references with image2 storyboards and Seedance 2.0.
---

# Seedance Storyboard Replication

Select the route from the provided inputs, enforce the route-specific approval gates, and use the bundled scripts only for deterministic media and API operations.
```

- [ ] **Step 4: Run the scaffold test and validator**

```bash
python3 -m unittest discover -s seedance-storyboard-replication/tests -p 'test_skill_contract.py' -v
python3 /Users/jiangyongjian/.codex/skills/.system/skill-creator/scripts/quick_validate.py seedance-storyboard-replication
```

Expected: one passing test and `Skill is valid!`.

- [ ] **Step 5: Commit the scaffold**

```bash
git add seedance-storyboard-replication/SKILL.md seedance-storyboard-replication/agents seedance-storyboard-replication/tests/test_skill_contract.py
git commit -m "feat: scaffold seedance storyboard replication skill"
```

### Task 2: Load the Single Private Configuration Safely

**Files:**
- Create: `seedance-storyboard-replication/scripts/config.py`
- Create: `seedance-storyboard-replication/references/seedance.env.example`
- Create: `seedance-storyboard-replication/tests/test_config.py`

- [ ] **Step 1: Write failing configuration tests**

```python
import os
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from config import ConfigurationError, load_settings  # noqa: E402


class ConfigTest(unittest.TestCase):
    def test_loads_jimmy_and_tkagent_cos_aliases_from_one_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "seedance.env"
            env_file.write_text(
                "JIMMYAI_API_KEY=jimmy-secret\n"
                "TKAGENT_COS_BUCKET=seedance-temp-1300000000\n"
                "TKAGENT_COS_REGION=ap-guangzhou\n"
                "TKAGENT_COS_SECRET_ID=cos-id\n"
                "TKAGENT_COS_SECRET_KEY=cos-key\n",
                encoding="utf-8",
            )
            settings = load_settings(env_file, environ={})

        self.assertEqual(settings.cos_bucket, "seedance-temp-1300000000")
        self.assertEqual(settings.cos_region, "ap-guangzhou")
        self.assertEqual(
            settings.cos_public_base_url,
            "https://seedance-temp-1300000000.cos.ap-guangzhou.myqcloud.com",
        )
        self.assertNotIn("jimmy-secret", repr(settings))
        self.assertNotIn("cos-key", repr(settings))

    def test_require_cos_names_missing_variables_without_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "seedance.env"
            env_file.write_text("JIMMYAI_API_KEY=set\n", encoding="utf-8")
            settings = load_settings(env_file, environ={})

        with self.assertRaisesRegex(ConfigurationError, "TENCENT_COS_BUCKET"):
            settings.require_cos()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_config.py -v
```

Expected: FAIL because `config.py` is absent.

- [ ] **Step 3: Implement the minimal settings loader**

Implement these exact public interfaces:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
import os


DEFAULT_ENV_FILE = Path.home() / ".codex" / "secrets" / "seedance.env"


class ConfigurationError(RuntimeError):
    pass


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
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
```

The example env file contains the exact variable names with empty values and no real credentials.

- [ ] **Step 4: Run tests and inspect permissions without printing values**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_config.py -v
stat -f '%OLp %Su' "$HOME/.codex/secrets/seedance.env"
```

Expected: tests PASS; local secret file reports mode `600` and the current user.

- [ ] **Step 5: Import existing COS variables into the one secret file without terminal output**

Only if `~/.codex/secrets/seedance.env` does not already contain a `TKAGENT_COS_` or `TENCENT_COS_` block, run:

```bash
rg '^TKAGENT_COS_' /Users/jiangyongjian/workspace/aiAgent/.env.local \
  >> "$HOME/.codex/secrets/seedance.env"
chmod 600 "$HOME/.codex/secrets/seedance.env"
```

Then add the non-secret override `TENCENT_COS_OBJECT_PREFIX=seedance-storyboard`. Do not print the file contents.

- [ ] **Step 6: Commit configuration code, never the private env file**

```bash
git add seedance-storyboard-replication/scripts/config.py seedance-storyboard-replication/references/seedance.env.example seedance-storyboard-replication/tests/test_config.py
git commit -m "feat: load seedance and COS configuration safely"
```

### Task 3: Implement the 17-Second Segment Planner

**Files:**
- Create: `seedance-storyboard-replication/scripts/segment_plan.py`
- Create: `seedance-storyboard-replication/tests/test_segment_plan.py`

- [ ] **Step 1: Write failing boundary tests**

```python
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
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

    def test_balances_eighteen_seconds_without_short_tail(self) -> None:
        plan = plan_segments([0, 4, 9, 13, 18])
        self.assertEqual(
            [(segment.source_start, segment.source_end) for segment in plan.segments],
            [(0, 9), (9, 18)],
        )

    def test_rejects_an_unsplittable_cut_longer_than_fifteen_seconds(self) -> None:
        with self.assertRaisesRegex(PlanningError, "split the Cut"):
            plan_segments([0, 18])
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_segment_plan.py -v
```

Expected: FAIL because `segment_plan.py` is absent.

- [ ] **Step 3: Implement deterministic partitioning**

Use dataclasses `Segment(source_start, source_end, output_duration)` and `SegmentPlan(total_source_duration, retime_scale, segments)`. Implement this algorithm:

```python
def plan_segments(boundaries: list[float]) -> SegmentPlan:
    validate_strictly_increasing(boundaries)
    total = boundaries[-1] - boundaries[0]
    if total <= 15:
        return one_segment(total, scale=1.0)
    if total <= 17:
        return one_segment(15, scale=15 / total)

    count = math.ceil(total / 15)
    target = total / count
    candidates = []
    for chosen in itertools.combinations(boundaries[1:-1], count - 1):
        points = [boundaries[0], *chosen, boundaries[-1]]
        durations = [right - left for left, right in zip(points, points[1:])]
        if all(5 <= duration <= 15 for duration in durations):
            score = sum((duration - target) ** 2 for duration in durations)
            candidates.append((score, points, durations))
    if not candidates:
        raise PlanningError(
            "No 5-15 second partition exists at the approved boundaries; split the Cut at an internal action beat."
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
```

Add a CLI accepting `--cuts-json` and writing `segment_plan.json` with source and segment-local time mappings.

- [ ] **Step 4: Run focused and edge-case tests**

Add cases for 20 seconds (`10 + 10`), 29 seconds (`14 + 15` when those boundaries exist), invalid duplicate boundaries, and any tail below five seconds. Then run:

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_segment_plan.py -v
```

Expected: all planner tests PASS.

- [ ] **Step 5: Commit the planner**

```bash
git add seedance-storyboard-replication/scripts/segment_plan.py seedance-storyboard-replication/tests/test_segment_plan.py
git commit -m "feat: plan seedance segments at approved cut boundaries"
```

### Task 4: Publish Local Media to Public Tencent COS URLs

**Files:**
- Create: `seedance-storyboard-replication/scripts/cos_publish.py`
- Create: `seedance-storyboard-replication/tests/test_cos_publish.py`

- [ ] **Step 1: Write failing publisher tests with a fake client**

```python
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cos_publish import CosPublisher, CosPublishError  # noqa: E402


class FakeCosClient:
    def __init__(self) -> None:
        self.uploads = []

    def upload_file(self, *, Bucket: str, LocalFilePath: str, Key: str) -> None:
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
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_cos_publish.py -v
```

Expected: FAIL because `cos_publish.py` is absent.

- [ ] **Step 3: Implement the publisher and CLI**

Use `qcloud_cos.CosConfig` and `CosS3Client` only in `from_settings()` so tests do not need network access. Public API:

```python
class CosPublisher:
    def __init__(self, bucket, public_base_url, object_prefix, client): ...

    @classmethod
    def from_settings(cls, settings, run_id: str): ...

    def publish(self, local_path: Path, object_key: str) -> str:
        if not local_path.is_file():
            raise CosPublishError(f"Media file not found: {local_path}")
        normalized = object_key.strip("/").replace("\\", "/")
        key = f"{self.object_prefix}/{normalized}" if self.object_prefix else normalized
        self.client.upload_file(Bucket=self.bucket, LocalFilePath=str(local_path), Key=key)
        return f"{self.public_base_url}/{quote(key, safe='/')}"
```

The CLI accepts repeated `--media PATH`, writes `published_media.json`, and prints only file names and URLs. It never prints COS credentials.

- [ ] **Step 4: Run tests and a non-network import check**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_cos_publish.py -v
python3 -c 'from qcloud_cos import CosConfig, CosS3Client; print("COS SDK ready")'
```

Expected: tests PASS and `COS SDK ready`.

- [ ] **Step 5: Commit the COS publisher**

```bash
git add seedance-storyboard-replication/scripts/cos_publish.py seedance-storyboard-replication/tests/test_cos_publish.py
git commit -m "feat: publish seedance references to Tencent COS"
```

### Task 5: Implement JimmyAI Task Creation, Resume, Poll, and Download

**Files:**
- Create: `seedance-storyboard-replication/scripts/seedance_submit.py`
- Create: `seedance-storyboard-replication/tests/test_seedance_submit.py`

- [ ] **Step 1: Write failing payload and polling tests**

```python
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from seedance_submit import (  # noqa: E402
    PayloadError,
    build_payload,
    parse_task_id,
    poll_task,
)


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
            build_payload("prompt", 10, "9:16", [f"https://x/{i}.png" for i in range(5)], ["https://x/ref.mp4"])

    def test_accepts_documented_success_code_variants(self) -> None:
        self.assertEqual(parse_task_id({"code": 0, "data": {"task_id": "a"}}), "a")
        self.assertEqual(parse_task_id({"code": "20000", "data": {"task_id": "b"}}), "b")
```

Add a fake transport that returns `queued`, `processing`, and `completed` responses, then assert `poll_task()` returns `data.result.video_url`. Add failure and timeout cases without sleeping by injecting `sleep=lambda _: None`.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_seedance_submit.py -v
```

Expected: FAIL because `seedance_submit.py` is absent.

- [ ] **Step 3: Implement validation and transport boundaries**

Implement:

```python
CREATE_PATH = "/api/open-api/v1/seedance/videos"
QUERY_PATH = "/api/open-api/v1/videos/{task_id}"
RUNNING = {"queued", "processing"}
FINAL = {"completed", "failed"}


def build_payload(prompt, duration, ratio, image_urls, reference_video_urls):
    if not prompt.strip() or len(prompt) > 5000:
        raise PayloadError("prompt must contain 1-5000 characters")
    if not 1 <= duration <= 15:
        raise PayloadError("duration must be between 1 and 15 seconds")
    if ratio not in {"16:9", "9:16", "1:1"}:
        raise PayloadError("ratio must be one of 16:9, 9:16, 1:1")
    if len(image_urls) > 4:
        raise PayloadError("seedance2.0-fast-md accepts at most 4 images")
    require_public_https_urls([*image_urls, *reference_video_urls])
    return {
        "model": "seedance2.0-fast-md",
        "prompt": prompt.strip(),
        "duration": duration,
        "ratio": ratio,
        "images": list(image_urls),
        "reference_videos": list(reference_video_urls),
    }
```

Create `JimmyAiClient` with injectable `request_json`, `download`, `sleep`, and `clock`. Retry only `429` and transient `5xx` responses with bounded exponential backoff. Treat `401/403` as non-retryable configuration errors.

CLI contract:

```text
--prompt-file PATH
--image-url URL                 repeatable, max 4
--reference-video-url URL       repeatable
--duration INTEGER
--ratio 9:16
--output-dir PATH
--env-file PATH                 defaults to ~/.codex/secrets/seedance.env
--dry-run
--poll
--resume-task-id ID
--timeout 1800
--poll-interval 20
```

Always write `request.redacted.json`, `create_response.json`, and `status.json`. Save the task ID before polling. On completion, download `data.result.video_url` to `result.mp4` immediately.

- [ ] **Step 4: Run all API tests**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_seedance_submit.py -v
```

Expected: payload, response variants, retries, polling, resume, failure, timeout, and mocked download tests PASS with zero real network calls.

- [ ] **Step 5: Commit the API client**

```bash
git add seedance-storyboard-replication/scripts/seedance_submit.py seedance-storyboard-replication/tests/test_seedance_submit.py
git commit -m "feat: submit and resume JimmyAI Seedance tasks"
```

### Task 6: Concatenate Segments While Preserving Audio

**Files:**
- Create: `seedance-storyboard-replication/scripts/concat_videos.py`
- Create: `seedance-storyboard-replication/tests/test_concat_videos.py`

- [ ] **Step 1: Write failing command and integration tests**

Test `probe_media()` rejects a segment without video, reports whether audio exists, and `concat_segments()` rejects mixed audio presence. The integration test creates two one-second 360x640 H.264/AAC fixtures:

```bash
ffmpeg -y -f lavfi -i color=c=red:s=360x640:d=1 -f lavfi -i sine=frequency=440:duration=1 \
  -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac segment-01.mp4
ffmpeg -y -f lavfi -i color=c=blue:s=360x640:d=1 -f lavfi -i sine=frequency=660:duration=1 \
  -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac segment-02.mp4
```

Then assert the result duration is between 1.8 and 2.2 seconds and FFprobe reports both video and audio streams.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_concat_videos.py -v
```

Expected: FAIL because `concat_videos.py` is absent.

- [ ] **Step 3: Implement probe, concat, and fallback behavior**

Use JSON FFprobe output:

```text
ffprobe -v error -show_streams -show_format -of json <segment>
```

First attempt lossless concatenation with a generated concat list:

```text
ffmpeg -y -f concat -safe 0 -i concat-list.txt -c copy final.mp4
```

If codecs, dimensions, or time bases differ, normalize every segment to H.264/AAC and concatenate the normalized files. Never silently remove audio. If the prompt requested audio and any segment lacks it, fail before concatenation with the segment path in the error.

- [ ] **Step 4: Run the real local FFmpeg tests**

```bash
python3 -m unittest seedance-storyboard-replication/tests/test_concat_videos.py -v
```

Expected: all tests PASS; final fixture contains one video and one audio stream.

- [ ] **Step 5: Commit media assembly**

```bash
git add seedance-storyboard-replication/scripts/concat_videos.py seedance-storyboard-replication/tests/test_concat_videos.py
git commit -m "feat: concatenate Seedance segments with audio"
```

### Task 7: Add Prompt References and the Complete Route Workflow

**Files:**
- Modify: `seedance-storyboard-replication/SKILL.md`
- Create: `seedance-storyboard-replication/references/fukeGem.md`
- Create: `seedance-storyboard-replication/references/daohuo_storyboard_prompt.md`
- Create: `seedance-storyboard-replication/references/seedance-prompt.md`
- Create: `seedance-storyboard-replication/references/jimmyai-api.md`
- Modify: `seedance-storyboard-replication/tests/test_skill_contract.py`
- Regenerate: `seedance-storyboard-replication/agents/openai.yaml`

- [ ] **Step 1: Extend the contract test and verify RED**

Add assertions for:

```python
def test_skill_declares_both_routes_and_approval_gates(self) -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for required in (
        "路线一：已有分镜脚本",
        "路线二：仅提供参考视频",
        "不要二次确认分镜脚本",
        "确认反解分镜脚本",
        "确认故事板",
        "image2",
        "reference_videos",
        "最多 4 张",
        "不默认添加背景音乐",
    ):
        self.assertIn(required, text)

def test_required_references_exist(self) -> None:
    for name in (
        "fukeGem.md",
        "daohuo_storyboard_prompt.md",
        "seedance-prompt.md",
        "jimmyai-api.md",
        "seedance.env.example",
    ):
        self.assertTrue((SKILL_ROOT / "references" / name).is_file())
```

Run the contract test and expect failures for missing route content and references.

- [ ] **Step 2: Copy the two approved prompts unchanged**

```bash
cp fukeGem.md seedance-storyboard-replication/references/fukeGem.md
cp daohuo_storyboard_prompt.md seedance-storyboard-replication/references/daohuo_storyboard_prompt.md
```

Do not copy `storyPrompt.md`.

- [ ] **Step 3: Write the Seedance prompt assembly reference**

`seedance-prompt.md` must require, in this order:

1. Actual image-number mapping with storyboard, optional character board, and one or two product boards.
2. Original reference-video mapping through `reference_videos`.
3. Global product and character identity locks.
4. Segment-local Cut timecodes and concrete camera/action direction.
5. Voiceover plus environment/action sound; no background music by default.
6. No subtitles, screen text, invented shots, reordered Cuts, product deformation, or identity drift.
7. Output under 5000 characters with no unresolved image-number or generic time placeholders.

Include one complete four-Cut example with concrete timecodes and actual `@图片1`/`@图片2` assignments.

- [ ] **Step 4: Write the concise JimmyAI reference**

Record the verified contract: create/query URLs, model, 1-15 seconds, fixed 720p, 5000 prompt characters, four images, public HTTPS media, no uploaded reference audio, `queued/processing/completed/failed`, result URL path, and three-day result retention. Include one redacted cURL example.

- [ ] **Step 5: Complete `SKILL.md` orchestration**

Keep it under 500 lines. Include these exact behavioral sections:

```markdown
## Route Selection
## Route 1: Existing Storyboard Script
## Route 2: Reference Video Only
## Storyboard Approval Loop
## Image Allocation Gate
## Duration Planning
## COS and Seedance Submission
## Download, Concatenation, and QC
## Failure and Resume Rules
```

Route 1 skips script confirmation and stops after every image2 storyboard revision. Route 2 stops after the fukeGem script and again after every storyboard revision. Both routes must wait for explicit approval before the paid Seedance call. Tell users about the four-image allocation before submission and ask them to prepare product boards when needed.

The COS submission section must state that the dedicated bucket is `公有读私有写`, that uploaded media uses anonymous public HTTPS URLs, and that product boards preserve the user's original product pixels rather than AI-redrawing the product. The final assembly section must require FFmpeg concatenation to preserve audio and fail when an expected segment audio stream is missing.

- [ ] **Step 6: Regenerate UI metadata and run contract tests**

```bash
python3 /Users/jiangyongjian/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py \
  seedance-storyboard-replication \
  --interface display_name="Seedance Storyboard Replication" \
  --interface short_description="复刻带货短视频并通过 Seedance 生成成片" \
  --interface default_prompt="使用参考视频、分镜脚本和产品素材生成故事板与 Seedance 成片。"
python3 -m unittest seedance-storyboard-replication/tests/test_skill_contract.py -v
python3 /Users/jiangyongjian/.codex/skills/.system/skill-creator/scripts/quick_validate.py seedance-storyboard-replication
```

Expected: contract tests PASS and skill validation succeeds.

- [ ] **Step 7: Commit the complete workflow**

```bash
git add seedance-storyboard-replication/SKILL.md seedance-storyboard-replication/agents seedance-storyboard-replication/references seedance-storyboard-replication/tests/test_skill_contract.py
git commit -m "feat: define storyboard replication routes and prompts"
```

### Task 8: Add Portable Installation and Health Checks

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `install.sh`
- Create: `check_install.sh`

- [ ] **Step 1: Write the install contract**

`.gitignore` must contain:

```gitignore
__pycache__/
*.pyc
outputs/
*.env
!*.env.example
```

`requirements.txt` contains:

```text
cos-python-sdk-v5
```

- [ ] **Step 2: Implement `install.sh`**

The script must:

1. Resolve its own directory.
2. Fail if Python 3, FFmpeg, or FFprobe is missing.
3. Report the exact `python3 -m pip install -r requirements.txt` command when `qcloud_cos` is missing; do not silently modify Python.
4. Copy `seedance-storyboard-replication/` to `${CODEX_HOME:-$HOME/.codex}/skills/seedance-storyboard-replication`.
5. Never copy or create a real env file.
6. Run `quick_validate.py` against the installed directory when the validator is available.

- [ ] **Step 3: Implement `check_install.sh`**

It checks and reports only `READY`, `MISSING`, or `INVALID` for:

- Installed `SKILL.md`.
- `JIMMYAI_API_KEY` presence in `~/.codex/secrets/seedance.env`.
- COS bucket, region, SecretId, and SecretKey presence through either `TENCENT_COS_*` or `TKAGENT_COS_*` aliases.
- Secret file mode `600`.
- `qcloud_cos`, FFmpeg, and FFprobe.

It must never echo any credential value.

- [ ] **Step 4: Test installation into an isolated CODEX_HOME**

```bash
tmp_home="$(mktemp -d)"
CODEX_HOME="$tmp_home" ./install.sh
test -f "$tmp_home/skills/seedance-storyboard-replication/SKILL.md"
rm -rf "$tmp_home"
```

Expected: installer succeeds without creating a secrets file.

- [ ] **Step 5: Commit packaging**

```bash
git add .gitignore requirements.txt install.sh check_install.sh
git commit -m "feat: package portable skill installation"
```

### Task 9: Run Full Verification and Install Locally

**Files:**
- Modify only files found defective by verification.

- [ ] **Step 1: Run the complete automated suite**

```bash
python3 -m unittest discover -s seedance-storyboard-replication/tests -p 'test_*.py' -v
```

Expected: all unit and local FFmpeg integration tests PASS with no JimmyAI or COS network calls.

- [ ] **Step 2: Run skill validation and placeholder scans**

```bash
python3 /Users/jiangyongjian/.codex/skills/.system/skill-creator/scripts/quick_validate.py seedance-storyboard-replication
rg -n '0:XX|具体秒数|@图片X|@图片N' seedance-storyboard-replication
```

Expected: validation succeeds. Placeholder matches are allowed only when a reference explicitly prohibits them; generated examples and executable artifacts contain none.

- [ ] **Step 3: Run deterministic dry runs**

Create temporary fixture URLs and a concrete prompt, then run:

```bash
python3 seedance-storyboard-replication/scripts/seedance_submit.py \
  --prompt-file /tmp/seedance-prompt.md \
  --image-url https://example.com/storyboard.png \
  --image-url https://example.com/product-board.jpg \
  --reference-video-url https://example.com/reference.mp4 \
  --duration 15 \
  --ratio 9:16 \
  --output-dir /tmp/seedance-dry-run \
  --dry-run
```

Expected: a valid `request.redacted.json` with model `seedance2.0-fast-md`, two images, one reference video, no resolution, and no reference audio.

- [ ] **Step 4: Install and check the local skill**

```bash
./install.sh
./check_install.sh
```

Expected: the skill, JimmyAI key, COS configuration, secret permissions, Python SDK, FFmpeg, and FFprobe all report `READY`.

- [ ] **Step 5: Verify the COS URL anonymously only after the bucket is configured**

Upload a harmless one-pixel fixture through `cos_publish.py`, then run `curl -I` on the returned URL without an Authorization header. Expected: HTTP `200`. Delete the fixture manually after the check.

- [ ] **Step 6: Do not spend JimmyAI credits without an explicit generation request**

Stop after dry-run verification unless the user explicitly asks for a paid smoke test. If requested, submit one short low-cost task, poll it, download immediately, and verify that the MP4 contains both video and audio.

- [ ] **Step 7: Review repository state and commit verification fixes**

```bash
git status --short
git diff --check
git log --oneline -10
```

Commit only necessary verification fixes. Leave the user's unrelated root-level files untouched.
