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
- Do not submit a newly assembled or modified Seedance request until the user has approved its exact prompt and request preview.

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
2. Plan the Seedance segments from the confirmed Cut boundaries.
3. Apply `daohuo_storyboard_prompt.md` and call Codex `image2` once per planned segment to generate the continuous storyboard set.
4. Show all segment boards and the continuity map to the user and stop.
5. Revise affected boards from the user's feedback until the user approves every board and cross-segment boundary.
6. Continue through the shared Seedance generation flow.

### Route 2: Reference Video Only

Inputs:

- Reference video.
- Optional character reference image or character board.
- Product reference images or one to two prepared product boards.

Flow:

1. Inspect the reference video and apply `fukeGem.md` to reverse-engineer its visual style, language, timing, shots, actions, camera movement, and spoken-copy intent.
2. Show the Chinese storyboard script to the user and stop.
3. Revise the script until the user explicitly approves it.
4. Plan the Seedance segments from the approved Cut boundaries.
5. Apply `daohuo_storyboard_prompt.md` and call Codex `image2` once per planned segment to generate the continuous storyboard set.
6. Show all segment boards and the continuity map to the user and stop again.
7. Revise affected boards until the user approves every board and cross-segment boundary.
8. Continue through the shared Seedance generation flow.

## Storyboard Generation and Revision

- Run duration planning before storyboard generation. A script with one Seedance segment gets one storyboard board; a script with multiple Seedance segments gets exactly one `16:9` storyboard board per segment and no additional master board.
- Treat all segment boards as one continuous storyboard set. Preserve global Cut numbering while also showing segment-local timecodes.
- Build a continuity manifest before calling `image2`. It locks character identity and wardrobe, product appearance and scale, environment and light direction, camera language, screen direction, and every segment boundary's outgoing action, incoming action, prop position, body pose, and audio handoff.
- Generate each segment board from the same approved script, character/product references, and continuity manifest. Segment 2 and later must also use the preceding segment board as continuity reference; they may not independently reinterpret the story.
- Keep Cut order, character identity, product identity, scene continuity, action order, camera logic, and visual style locked to the approved script and references.
- Store each user-visible revision as `storyboards/segment_01_v1.png`, `storyboards/segment_02_v1.png`, and so on.
- For broad feedback, regenerate the complete storyboard set with `image2`.
- For feedback limited to one segment, regenerate only that segment board with `image2`, using the approved references and adjacent board for continuity. Recheck and reapprove both sides of any changed segment boundary.
- Never use AI to create a product board. A product board must be a layout of unchanged user product images.
- Present every segment board together with the segment map. Do not continue to Seedance until the user explicitly approves every board and the set-wide continuity.

## Shared Generation Flow

After the required approvals:

1. Normalize the approved script into structured Cut data with global timecodes, shot descriptions, voiceover, environment sound, and action sound.
2. Plan one or more Seedance segments.
3. Generate one storyboard board per planned segment from a shared continuity manifest, then stop until every board and all cross-segment boundaries are approved.
4. Generate one concrete Seedance prompt per segment. Each prompt contains only that segment's Cuts, plus explicit incoming/outgoing continuity anchors. Prompts request voiceover, environment sound, and action sound by default, but do not request background music unless the user asks for it.
5. Validate image allocation separately for every segment.
6. Upload each approved segment storyboard, optional character board, and product boards to Tencent COS. Keep the original reference video local; it is never sent to Seedance.
7. Build redacted request previews and report every exact prompt, segment-specific image mapping, task count, ratio, and planned segment duration.
8. Stop at the **确认 Seedance 提示词** gate. Each segment preview receives its own SHA-256 digest; any prompt, board, image mapping, duration, ratio, or segmentation change invalidates the affected approval.
9. Submit `seedance2.0-fast-md` tasks only after the user explicitly approves the complete set of exact previews. Resume polling an existing task without a new approval because resumption does not create a new paid task.
10. Poll each task through `queued` and `processing` until `completed` or `failed`.
11. Download every completed result immediately because JimmyAI result URLs expire after about three days.
12. Concatenate multiple segments with FFmpeg at the approved natural Cut boundary, preserving their audio tracks. Do not add a crossfade by default.
13. Run final media checks and retain all diagnostic artifacts required for retry or resumption.

## Duration and Segmentation Rules

- Reject reference videos longer than 30 seconds before reverse engineering or storyboard generation.
- Tell the user immediately after upload: videos up to 15 seconds are the most stable because they use one storyboard and one generation; videos from more than 17 through 30 seconds require two separately generated clips and a natural story handoff. A 30-second video must support a handoff at 15 seconds.
- For a total duration up to 15 seconds, preserve the requested duration and submit one task.
- For a total duration greater than 15 and no greater than 17 seconds, retime all Cuts proportionally into one 15-second task.
- For a total duration greater than 17 and no greater than 30 seconds, create exactly two segments and exactly two storyboard boards. Never create a third segment or third storyboard board.
- Narrative analysis must select one explicit `split_boundary` before duration planning. The planner validates this selected point; it must never choose a boundary merely because it balances durations.
- The legal split interval is `max(5, total - 15)` through `min(15, total - 5)`. For 25 seconds this is 10-15 seconds; for 27 seconds it is 12-15 seconds; for 30 seconds it is exactly 15 seconds.
- Within that legal interval, choose the point that best completes an action, spoken sentence, story beat, scene transition, or deliberate visual transition. Character state, product position, screen direction, light, environment sound, and voiceover cadence must support the handoff.
- If no approved Cut boundary works, identify an internal action beat inside the relevant Cut, revise the script boundary, and stop for user approval. If no natural internal beat works, stop and explain that the source cannot be generated faithfully under the two-segment limit; never hard-cut or add a third segment.
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
- `reference_videos`: never include this field. Both routes use the fixed B workflow after real QC showed that passing the source video can override the target character identity.
- Do not include `reference_audios`; MD does not accept uploaded reference audio.
- Do not send `resolution`; MD output is fixed at 720p.
- Do not combine `images` with `first_image` or `last_image`.

The generated output is expected to contain model-generated audio. The skill must preserve it during download and concatenation. It must not rely on uploading a reference audio file.

Accept the documented success response variants defensively, extract `data.task_id`, and redact authorization headers and secrets from saved requests. Poll statuses are `queued`, `processing`, `completed`, and `failed`. The final video URL is `data.result.video_url`.

## Image Allocation

The normal four-image allocation is:

1. The approved storyboard board for the current segment only.
2. Optional character reference board.
3. Product reference board 1.
4. Optional product reference board 2.

Never send a whole-video storyboard to every task in a multi-segment run. Segment 1 receives segment board 1, segment 2 receives segment board 2, and so on. Shared character and product boards may be reused across tasks.

The reference video is used only for upstream reverse engineering and storyboard generation. It is not uploaded to COS for Seedance and is not sent through `reference_videos`.

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
├── continuity_manifest.json
├── storyboards/
│   ├── segment_01_v1.png
│   └── segment_02_v1.png
├── segment_plan.json
├── segments/
│   ├── 01/
│   │   ├── seedance_prompt.md
│   │   ├── request.redacted.json
│   │   ├── approval_preview.json
│   │   └── failure.json
│   └── 02/
│       ├── seedance_prompt.md
│       ├── request.redacted.json
│       ├── approval_preview.json
│       └── failure.json
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
- Classify `PROVIDER_MODERATION_ERROR: TRADEMARK` as a non-retryable trademark moderation failure. Explain that the storyboard prompt and/or image assets require review, return to storyboard generation and approval, and never imply that prompt wording can bypass provider moderation. Do not silently remove a user product logo; request approval before using a compliant debranded or replacement asset.
- Classify `Read timed out`, media `s3 upload failed`, and `connection reset by peer` as transient provider media-fetch failures. Keep the exact request unchanged and wait for explicit user confirmation before creating a replacement paid task.
- Classify `video_reference ... DURATION_TOO_LONG` as an outdated fixed-B request. Report the offending reference-video field and rebuild without `reference_videos`; if a different future workflow intentionally sends a reference video, it must be at most 15 seconds.
- Unknown provider failures are not automatically retried. Preserve the raw message and ask the user before any new paid submission.
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
- Image count validation and rejection of any attempted `reference_videos` payload.
- Rejection of `reference_audios`, `resolution`, and incompatible frame/image modes.
- COS object-key normalization, URL encoding, and public URL construction.
- JimmyAI response parsing, polling, retry, timeout, failure, and download behavior.
- Exact-request SHA-256 approval enforcement and approval invalidation after any request change.
- Trademark moderation, transient media-fetch timeout, and stale reference-video duration failure classification.
- Request redaction.
- FFmpeg concatenation with video and audio streams.
- Skill route selection and the route-specific approval gates.
- Required prompt references and the absence of unresolved placeholders in generated artifacts.

Integration checks use mocked network clients by default. A real JimmyAI generation is a paid smoke test and runs only when the user has configured their own credentials and explicitly requests submission.
