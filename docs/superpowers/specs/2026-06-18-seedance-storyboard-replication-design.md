# Seedance Storyboard Replication Skill Design

## Goal

Build an installable Codex skill named `seedance-storyboard-replication` for replicating ecommerce short videos with storyboard images and JimmyAI's `seedance2.0-fast-md` API.

The skill must support two user routes, use Codex `image2` for storyboard generation, publish local media to Tencent COS, submit and poll JimmyAI tasks, download results immediately, and concatenate long outputs with FFmpeg.

## Non-goals

- Do not build a standalone web application or persistent job service.
- Do not call the Volcano Ark Seedance API.
- Do not upload reference audio to the MD API.
- Do not use AI to redraw or reinterpret product reference boards.
- Do not bypass the user approval gates for scripts or storyboards.

## Skill Layout

```text
seedance-storyboard-replication/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── fukeGem.md
│   ├── daohuo_storyboard_prompt.md
│   ├── seedance-prompt.md
│   └── jimmyai-api.md
├── scripts/
│   ├── cos_publish.py
│   ├── seedance_submit.py
│   ├── segment_plan.py
│   └── concat_videos.py
└── tests/
```

The repository will also include portable installation helpers that copy the skill into `~/.codex/skills/` and never package a real credential file.

## Route Selection

### Route 1: Existing Storyboard Script

Inputs:

- Reference video.
- A storyboard script that the user has already approved.
- Optional character reference image or character board.
- Product reference images or one to two prepared product boards.

Flow:

1. Treat the supplied storyboard script as final. Do not ask the user to approve it again.
2. Apply `daohuo_storyboard_prompt.md` and call Codex `image2` to generate the storyboard image.
3. Show the storyboard to the user and stop.
4. Revise the storyboard from the user's feedback until the user explicitly approves it.
5. Continue through the shared Seedance generation flow.

### Route 2: Reference Video Only

Inputs:

- Reference video.
- Optional character reference image or character board.
- Product reference images or one to two prepared product boards.

Flow:

1. Inspect the reference video and apply `fukeGem.md` to reverse-engineer its visual style, language, timing, shots, actions, camera movement, and spoken-copy intent.
2. Show the Chinese storyboard script to the user and stop.
3. Revise the script until the user explicitly approves it.
4. Apply `daohuo_storyboard_prompt.md` and call Codex `image2` to generate the storyboard image.
5. Show the storyboard to the user and stop again.
6. Revise the storyboard until the user explicitly approves it.
7. Continue through the shared Seedance generation flow.

## Storyboard Generation and Revision

- Generate one complete storyboard overview image on the first pass with Codex `image2`.
- Keep Cut order, character identity, product identity, scene continuity, action order, camera logic, and visual style locked to the approved script and references.
- Store each user-visible revision as `storyboard_v1.png`, `storyboard_v2.png`, and so on.
- For broad feedback, regenerate the complete storyboard with `image2`.
- For feedback limited to a small number of Cuts, regenerate only those Cuts with `image2`, using the approved references and current storyboard for continuity, then deterministically rebuild the overview image.
- Never use AI to create a product board. A product board must be a layout of unchanged user product images.
- Do not continue to Seedance until the user explicitly approves the current storyboard.

## Shared Generation Flow

After the required approvals:

1. Normalize the approved script into structured Cut data with global timecodes, shot descriptions, voiceover, environment sound, and action sound.
2. Plan one or more Seedance segments.
3. Generate one concrete Seedance prompt per segment. Prompts request voiceover, environment sound, and action sound by default, but do not request background music unless the user asks for it.
4. Validate the image reference allocation.
5. Upload the reference video, approved storyboard, optional character board, and product boards to Tencent COS.
6. Build a redacted request preview and report the task count and planned segment durations.
7. Submit `seedance2.0-fast-md` tasks after the user has requested generation and approved the storyboard.
8. Poll each task through `queued` and `processing` until `completed` or `failed`.
9. Download every completed result immediately because JimmyAI result URLs expire after about three days.
10. Concatenate multiple segments with FFmpeg, preserving their audio tracks.
11. Run final media checks and retain all diagnostic artifacts required for retry or resumption.

## Duration and Segmentation Rules

- For a total duration up to 15 seconds, preserve the requested duration and submit one task.
- For a total duration greater than 15 and no greater than 17 seconds, retime all Cuts proportionally into one 15-second task.
- For a total duration greater than 17 seconds, partition contiguous Cuts into segments between 5 and 15 seconds.
- Prefer existing Cut boundaries and keep complete actions and voiceover sentences together.
- Choose the minimum number of segments that satisfies the 15-second maximum, then prefer balanced segment durations near `total_duration / segment_count`.
- If a single Cut exceeds 15 seconds, split it at an internal action or camera beat.
- Never create a trailing segment shorter than 5 seconds. Move the preceding boundary earlier until all segments satisfy the range.
- Convert global timecodes to segment-local timecodes in each Seedance prompt while retaining a global-to-local mapping artifact.
- FFmpeg concatenation starts only after every segment has completed and downloaded successfully.

## JimmyAI API Contract

Create endpoint:

```text
POST https://www.jimmyai.cn/api/open-api/v1/seedance/videos
```

Query endpoint:

```text
GET https://www.jimmyai.cn/api/open-api/v1/videos/{task_id}
```

Create payload rules:

- `model`: always `seedance2.0-fast-md` unless a future explicit configuration changes it.
- `prompt`: required and at most 5000 characters.
- `duration`: required and between 1 and 15 seconds.
- `ratio`: `9:16` by default.
- `images`: public HTTPS URLs, at most four.
- `reference_videos`: include the public COS URL of the original reference video.
- Do not include `reference_audios`; MD does not accept uploaded reference audio.
- Do not send `resolution`; MD output is fixed at 720p.
- Do not combine `images` with `first_image` or `last_image`.

The generated output is expected to contain model-generated audio. The skill must preserve it during download and concatenation. It must not rely on uploading a reference audio file.

Accept the documented success response variants defensively, extract `data.task_id`, and redact authorization headers and secrets from saved requests. Poll statuses are `queued`, `processing`, `completed`, and `failed`. The final video URL is `data.result.video_url`.

## Image Allocation

The normal four-image allocation is:

1. Approved storyboard overview image.
2. Optional character reference board.
3. Product reference board 1.
4. Optional product reference board 2.

The reference video is sent through `reference_videos` and does not consume an image slot.

Before API submission, clearly tell the user that JimmyAI MD accepts no more than four reference images. When product reference material exceeds the available slots, stop and ask the user to prepare one or two product boards. Product boards must preserve original pixels and may only arrange, resize, label outside the product area, or add neutral spacing; they must not redraw the product.

## Tencent COS Publishing

Use the Tencent COS Python SDK to upload each local media file. Keep the implementation simple:

- The configured bucket or CDN/custom domain must allow anonymous public reads.
- Construct the result as `TENCENT_COS_PUBLIC_BASE_URL/<URL-encoded-object-key>`.
- Do not create presigned URLs.
- Use a unique run prefix under `TENCENT_COS_OBJECT_PREFIX` to avoid collisions.
- Verify configuration before uploading and fail with named missing variables.
- Do not delete source or uploaded media automatically.

## Configuration

Private configuration path:

```text
~/.codex/secrets/seedance.env
```

Use this existing file as the only private configuration source. Do not create a separate `seedance-storyboard.env` file.

Supported variables:

```dotenv
JIMMYAI_API_KEY=
JIMMYAI_BASE_URL=https://www.jimmyai.cn
TENCENT_COS_SECRET_ID=
TENCENT_COS_SECRET_KEY=
TENCENT_COS_BUCKET=
TENCENT_COS_REGION=
TENCENT_COS_PUBLIC_BASE_URL=
TENCENT_COS_OBJECT_PREFIX=seedance-storyboard
```

No real secret file may be committed, copied into the skill, logged, or included in a distributable archive. Provide only an example configuration file with empty values.

## Output Contract

Each run uses a dedicated output directory:

```text
outputs/<run-name>/
├── script.md
├── script.json
├── storyboard_v1.png
├── storyboard_v2.png
├── seedance_prompt.md
├── segment_plan.json
├── request.redacted.json
├── segments/
│   ├── 01/
│   └── 02/
└── final.mp4
```

Route 1 stores the user-supplied approved script. Route 2 stores every approved reverse-engineered script version needed for traceability. The final user-facing response emphasizes the approved storyboard, final prompt, downloaded video, and QC result rather than internal analysis artifacts.

## Error Handling and Resumption

- Reject missing files, empty prompts, invalid durations, unsupported ratios, and more than four images before any paid API call.
- Verify that the COS public base URL is HTTPS and that generated object URLs are syntactically valid.
- Treat `401` and `403` as credential or account-access errors without retrying.
- Retry `429` and transient `5xx` responses a small, bounded number of times with backoff.
- Save every task ID and latest status so polling can resume without creating a duplicate paid task.
- On timeout, preserve task state and print the exact resume command.
- On task failure, preserve the provider error and all successful sibling segments.
- Do not concatenate if any required segment is missing or failed.
- Download completed results immediately and report download failures separately from generation failures.

## Final Quality Checks

Use `ffprobe` and extracted review frames to check:

- Expected total duration within a small encoding tolerance.
- 9:16 orientation and 720p-class output.
- Presence of an audio stream when the prompt requested generated audio.
- Segment order and successful concatenation.
- No missing or reordered approved Cuts.
- Character and product continuity.
- No unintended subtitles, screen text, product deformation, or unrelated scenes.

Missing expected audio, missing Cuts, serious product drift, or failed concatenation is a failed result and must be reported rather than described as complete.

## Tests

Automated tests cover:

- Duration planning at 15, 17, 18, 20, and 29 seconds.
- Natural Cut boundary selection and the five-second minimum.
- Image count validation and `reference_videos` payload construction.
- Rejection of `reference_audios`, `resolution`, and incompatible frame/image modes.
- COS object-key normalization, URL encoding, and public URL construction.
- JimmyAI response parsing, polling, retry, timeout, failure, and download behavior.
- Request redaction.
- FFmpeg concatenation with video and audio streams.
- Skill route selection and the route-specific approval gates.
- Required prompt references and the absence of unresolved placeholders in generated artifacts.

Integration checks use mocked network clients by default. A real JimmyAI generation is a paid smoke test and runs only when the user has configured their own credentials and explicitly requests submission.
