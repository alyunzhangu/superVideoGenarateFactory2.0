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

## Route 1: Existing Storyboard Script

Use this route when the user already uploaded or pasted a confirmed storyboard script.

1. Read `references/daohuo_storyboard_prompt.md`.
2. Use `image2` directly to generate one `16:9 横版电影制作板` from the confirmed script plus product/person references.
3. Stop after generation for **确认故事板**. Ask whether the storyboard is approved for Seedance or needs changes.
4. If the user requests changes, revise only the storyboard image according to their notes and stop again for approval.
5. Only after explicit user approval, assemble the Seedance prompt and proceed to COS and Seedance submission.

Do not ask the user to reconfirm the script in this route. The only creative approval loop is the storyboard image.

## Route 2: Reference Video Only

Use this route when the user has only the reference video plus character/product references.

1. Read `references/fukeGem.md`.
2. Reverse-engineer the reference video into the Chinese storyboard script requested by `fukeGem.md`.
3. Stop for **确认反解分镜脚本**. Do not generate storyboard images yet.
4. After script approval, read `references/daohuo_storyboard_prompt.md` and use `image2` to generate one `16:9 横版电影制作板`.
5. Stop for **确认故事板**. Revise with `image2` as many times as needed until the user explicitly approves.
6. Only after explicit approval, assemble the Seedance prompt and proceed to COS and Seedance submission.

## Storyboard Approval Loop

The storyboard is the main user-facing quality gate.

- Use `image2` for storyboard image generation and targeted revisions.
- Generate one `16:9 横版电影制作板` first, not separate images per Cut. The board must include character/style reference, person detail close-ups, product reference, environment/movement plan, storyboard frames, lighting/mood notes, audio/tone notes, and cinematography notes.
- Preserve the confirmed Cut order. Do not invent shots, reorder Cuts, or turn product scenes into unrelated lifestyle scenes.
- Product fidelity matters more than visual novelty. Product boards must preserve the user's original product pixels rather than AI-redrawing the product.
- Every time a new storyboard image is produced, stop and ask the user to approve it before paid video generation.

## Image Allocation Gate

Before calling Seedance, explicitly map the image references:

- `@图片1`: approved storyboard overview image.
- `@图片2`: optional character board if a stable person identity is needed.
- `@图片3`: product board 1.
- `@图片4`: optional product board 2.

The original reference video is uploaded separately through `reference_videos`, not counted inside the four image slots. If there are too many product photos, instruct the user to combine them into one or two product boards before submission.

## Duration Planning

Use `scripts/segment_plan.py` after the script has approved Cut boundaries.

- Total duration `<= 15s`: submit one Seedance task at the source duration.
- Total duration `> 15s` and `<= 17s`: submit one 15-second task and compress timing into 15 seconds.
- Total duration `> 17s`: split only on approved Cut boundaries into 5-15 second segments. No segment may be shorter than 5 seconds or longer than 15 seconds.
- If no valid split exists, ask the user to split the long Cut at a visible action beat before continuing.

## COS and Seedance Submission

Read `references/seedance-prompt.md` and `references/jimmyai-api.md` before assembling the final request.

1. Confirm the user approved the storyboard and understands the four-image allocation.
2. Upload the reference video, approved storyboard image, character board, and product board(s) with `scripts/cos_publish.py`.
3. The dedicated COS bucket should be `公有读私有写`. Uploaded media uses anonymous public HTTPS URLs, not presigned URLs.
4. Build the prompt under 5000 characters. Include the actual `@图片1` to `@图片4` mapping, Cut-local timecodes, product/person identity locks, camera/action directions, voiceover, and real environment/action sound.
5. Do not use `reference_audios`; JimmyAI does not accept uploaded reference audio for this route.
6. Audio policy: request voiceover plus environment/action sound, and **不默认添加背景音乐** unless the user explicitly asks for music.
7. Call `scripts/seedance_submit.py` with `model=seedance2.0-fast-md`, `ratio=9:16`, `duration=1-15`, `images`, and `reference_videos`.

Never make a paid Seedance call until the user has explicitly approved the latest storyboard.

## Download, Concatenation, and QC

When a Seedance task completes, immediately download `data.result.video_url` to `result.mp4`.

- For a single task, probe the MP4 with `scripts/concat_videos.py` or FFprobe and confirm a video stream exists.
- For multiple segments, concatenate with FFmpeg through `scripts/concat_videos.py` and preserve audio.
- If audio was requested and any expected segment audio stream is missing, fail before concatenation and report the segment path.
- After concatenation, verify the final MP4 has video, has expected audio, and roughly matches the planned duration.

## Failure and Resume Rules

- Save `task_id.txt`, `request.redacted.json`, `create_response.json`, and `status.json` for each run.
- Use `--resume-task-id` to continue a known JimmyAI task instead of submitting a duplicate paid task.
- Retry only 429 and transient 5xx API responses. Treat 401/403 as configuration errors.
- If COS upload fails, do not submit Seedance.
- If storyboard approval is unclear, stop and ask for approval instead of assuming.
- Never print or copy real credentials. The skill reads only `~/.codex/secrets/seedance.env`.
