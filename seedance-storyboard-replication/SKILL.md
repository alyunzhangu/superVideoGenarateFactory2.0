---
name: seedance-storyboard-replication
description: Use when a user wants to replicate an ecommerce short video from a reference video, an approved storyboard script, character references, or product references with image2 storyboards and Seedance 2.0.
---

# Seedance Storyboard Replication

Turn a reference ecommerce short video into an approved image2 storyboard and a `seedance2.0-fast-md` video task. The skill owns route selection, approval gates, prompt assembly, public COS media publishing, Seedance submission, and final QC.

## Route Selection

Pick exactly one route from the user inputs:

- **路线一：已有分镜脚本**: the user provides a reference video, a confirmed storyboard script, and character/product images. Use the script as final. **不要二次确认分镜脚本**.
- **路线二：仅提供参考视频**: the user provides a reference video and character/product images, but no approved storyboard script. Use `references/fukeGem.md` to reverse-engineer the reference video, then stop for **确认反解分镜脚本** before storyboard generation.

Both routes must tell the user before Seedance submission that `seedance2.0-fast-md` accepts **最多 4 张** image references in `images`: one storyboard image, optional one character board, and one or two product boards. If product assets exceed the remaining slots, ask the user to prepare a product board that combines product photos while preserving product pixels.

Both routes use the **固定 B 方案**. 参考视频仅用于反解分镜、节奏分析和故事板生成; keep it local after the storyboard is approved. 禁止上传参考视频到 COS, and 禁止发送 `reference_videos` to Seedance. This rule also applies to Route 1 even when the user supplied an approved script together with a reference video.

## Route 1: Existing Storyboard Script

Use this route when the user already uploaded or pasted a confirmed storyboard script.

1. Read `references/daohuo_storyboard_prompt.md`.
2. Use `image2` directly to generate one `16:9 横版电影制作板` from the confirmed script, local reference video/frames, and product/person references.
3. Stop after generation for **确认故事板**. Ask whether the storyboard is approved for Seedance or needs changes.
4. If the user requests changes, revise only the storyboard image according to their notes and stop again for approval.
5. Only after explicit storyboard approval, assemble the complete Seedance prompt from the approved script plus storyboard/person/product images, then stop for **确认 Seedance 提示词** before any API submission.

Do not ask the user to reconfirm the script in this route. The only creative approval loop is the storyboard image.

## Route 2: Reference Video Only

Use this route when the user has only the reference video plus character/product references.

1. Read `references/fukeGem.md`.
2. Reverse-engineer the reference video into the Chinese storyboard script requested by `fukeGem.md`.
3. Stop for **确认反解分镜脚本**. Do not generate storyboard images yet.
4. After script approval, read `references/daohuo_storyboard_prompt.md` and use `image2` to generate one `16:9 横版电影制作板`.
5. Stop for **确认故事板**. Revise with `image2` as many times as needed until the user explicitly approves.
6. Only after explicit storyboard approval, assemble the complete Seedance prompt from the approved script plus storyboard/person/product images, then stop for **确认 Seedance 提示词** before any API submission.

## Storyboard Approval Loop

The storyboard is the main user-facing quality gate.

- Use `references/daohuo_storyboard_prompt.md` as the only storyboard prompt source. Follow its **固定骨架 + 动态填充** contract: keep the layout and constraints fixed, then replace every placeholder with the current approved script, character, product, reference-video role, and exact short labels before calling image2. Never maintain or improvise a second generic storyboard prompt.
- Use `image2` for storyboard image generation and targeted revisions.
- Generate one `16:9 横版电影制作板` first, not separate images per Cut. The board must include character/style reference, person detail close-ups, product reference, environment/movement plan, storyboard frames, lighting/mood notes, audio/tone notes, and cinematography notes.
- 故事板图片只承载视觉参考和重要事项。Each Cut card may show only its Cut number, time range, one short key action, and one critical identity/product constraint. Do not typeset the full script, long voiceover, or dense production notes into the generated image.
- Treat the approved script as the source of truth. 完整分镜脚本必须作为文本写入 Seedance prompt, including every Cut's script description, camera/action direction, voiceover, sound, continuity, and negative constraints.
- 不要让 Seedance 从故事板图片中识别完整脚本. The storyboard image is a visual reference, not a text transport. If image2 deforms a short label, remove it or add it later with deterministic typography; never preserve garbled text for submission.
- Preserve the confirmed Cut order. Do not invent shots, reorder Cuts, or turn product scenes into unrelated lifestyle scenes.
- Product fidelity matters more than visual novelty. Product boards must preserve the user's original product pixels rather than AI-redrawing the product.
- Every time a new storyboard image is produced, stop and ask the user to approve it before paid video generation.

## Image Allocation Gate

Before calling Seedance, explicitly map the image references:

- `@图片1`: approved storyboard overview image.
- `@图片2`: optional character board if a stable person identity is needed.
- `@图片3`: product board 1.
- `@图片4`: optional product board 2.

The reference video is an upstream analysis input only. Keep it local and do not publish it for Seedance. If there are too many product photos, instruct the user to combine them into one or two product boards before submission.

## Seedance Prompt Approval Gate

Both Route 1 and Route 2 must pass **确认 Seedance 提示词** after the latest storyboard approval.

1. Assemble the 完整 Seedance 提示词 and final payload, then run `scripts/seedance_submit.py --dry-run`.
2. Show the user the exact full prompt, 图片映射, model, ratio, duration, 时长和分段计划, and the image-only fixed-B request preview.
3. Save `approval_preview.json` and show its 请求摘要哈希. Stop and ask the user to approve this exact request.
4. Before explicit approval, 不得调用 Seedance or create any new paid task.
5. After the user says **确认 Seedance 提示词**, submit with `--approved-request-sha256` set to the preview digest.
6. 任何提示词或请求参数变化都会使旧确认失效. Rebuild the preview and stop for approval again. Resuming an already-created task ID is not a new paid submission and does not need another prompt approval.

## Duration Planning

Use `scripts/segment_plan.py` after the script has approved Cut boundaries.

- Total duration `<= 15s`: submit one Seedance task at the source duration.
- Total duration `> 15s` and `<= 17s`: submit one 15-second task and compress timing into 15 seconds.
- Total duration `> 17s`: split only on approved Cut boundaries into 5-15 second segments. No segment may be shorter than 5 seconds or longer than 15 seconds.
- If no valid split exists, ask the user to split the long Cut at a visible action beat before continuing.

## COS and Seedance Submission

Read `references/seedance-prompt.md` and `references/jimmyai-api.md` before assembling the final request.

1. Confirm the user approved the storyboard and understands the four-image allocation.
2. Upload only the approved storyboard image, character board, and product board(s) with `scripts/cos_publish.py`. 禁止上传参考视频到 COS.
3. The dedicated COS bucket should be `公有读私有写`. Uploaded media uses anonymous public HTTPS URLs, not presigned URLs.
4. Build the prompt under 5000 characters. Repeat the complete approved script as text, with the actual `@图片1` to `@图片4` mapping and, for every Cut, local timecode, 脚本描述, camera/action direction, product/person identity lock, 口播内容, sound, continuity, and 备注. Never replace these fields with “follow the storyboard image.”
5. Do not use `reference_audios`; JimmyAI does not accept uploaded reference audio for this route.
6. Audio policy: request voiceover plus environment/action sound, and **不默认添加背景音乐** unless the user explicitly asks for music.
7. Run a dry-run, expose the exact prompt/request and `approval_preview.json`, then stop for **确认 Seedance 提示词**.
8. Only after the matching 请求摘要哈希 is approved, call `scripts/seedance_submit.py` with `model=seedance2.0-fast-md`, `ratio=9:16`, `duration=1-15`, `images`, and `--approved-request-sha256`. 禁止发送 `reference_videos`.

Never make a paid Seedance call until the user has explicitly approved both the latest storyboard and the exact Seedance prompt preview.

## Download, Concatenation, and QC

When a Seedance task completes, immediately download `data.result.video_url` to `result.mp4`.

- For a single task, probe the MP4 with `scripts/concat_videos.py` or FFprobe and confirm a video stream exists.
- For multiple segments, concatenate with FFmpeg through `scripts/concat_videos.py` and preserve audio.
- If audio was requested and any expected segment audio stream is missing, fail before concatenation and report the segment path.
- After concatenation, verify the final MP4 has video, has expected audio, and roughly matches the planned duration.

## Failure and Resume Rules

- Save `task_id.txt`, `request.redacted.json`, `approval_preview.json`, `create_response.json`, `status.json`, and `failure.json` when applicable.
- Use `--resume-task-id` to continue a known JimmyAI task instead of submitting a duplicate paid task.
- Retry only 429 and transient 5xx API responses. Treat 401/403 as configuration errors.
- If COS upload fails, do not submit Seedance.
- If a planned or dry-run payload contains `reference_videos`, stop before submission and rebuild it with the fixed B route.
- `[SY_ERR:10] PROVIDER_MODERATION_ERROR: TRADEMARK`: do not retry unchanged. Clearly report the trademark moderation point, return to the storyboard prompt/image approval loop, and explain that changing the prompt may not be enough when the uploaded product image itself contains the mark. Never silently remove a product logo; obtain user approval before a compliant debranded or replacement asset is used.
- A bare `[SY_ERR:10] PROVIDER_MODERATION_ERROR` has no known subtype. Report it as an unspecified moderation failure and preserve the raw message; never infer `TRADEMARK` unless the provider returned that token.
- `[SY_ERR:10] Read timed out`, `s3 upload failed`, or `connection reset by peer`: treat as a transient provider media-fetch failure. Do not change the prompt. Preserve the original request and only create a replacement paid task after 用户明确确认.
- `video_reference ... DURATION_TOO_LONG`: report that the old request is still sending a reference video. The fixed B route must remove `reference_videos`; only a different intentional reference-video workflow would shorten it to 15 seconds or less.
- Unknown provider failures are never automatically resubmitted. Preserve the raw message in `failure.json` and tell the user what failed.
- If storyboard approval is unclear, stop and ask for approval instead of assuming.
- Never print or copy real credentials. The skill reads only `~/.codex/secrets/seedance.env`.
