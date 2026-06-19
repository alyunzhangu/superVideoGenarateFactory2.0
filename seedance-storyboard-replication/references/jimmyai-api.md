# JimmyAI Seedance 2.0 Fast MD API Reference

Use this contract for the bundled `scripts/seedance_submit.py` client.

- Create task: `POST https://www.jimmyai.cn/api/open-api/v1/seedance/videos`
- Query task: `GET https://www.jimmyai.cn/api/open-api/v1/videos/{task_id}`
- Model: `seedance2.0-fast-md`
- Duration: integer `1-15` seconds per task.
- Resolution: fixed 720p; do not send a `resolution` field.
- Prompt: maximum 5000 characters.
- Ratio: use `9:16` for ecommerce vertical videos unless the user asks otherwise.
- Images: `images` accepts at most four public HTTPS image URLs.
- Fixed workflow: use the **固定 B 方案**. The API supports optional reference videos, but this skill does not use them because they caused source-person identity drift during real QC. 不要发送 `reference_videos`.
- Reference audio: do not send uploaded reference audio; no `reference_audios` field.
- Media URLs: must be anonymous public HTTPS URLs, typically Tencent COS object URLs.
- Statuses: `queued`, `processing`, `completed`, `failed`.
- Result video URL path: `data.result.video_url`.
- Result retention: download promptly; JimmyAI result links are documented as retained for about three days.

## Approval Before Create

Run `seedance_submit.py --dry-run` first and expose the complete prompt, image mapping, duration, ratio, segmentation, `request.redacted.json`, and `approval_preview.json` to the user. A new paid create requires `--approved-request-sha256` matching that exact preview. Any prompt or payload change invalidates the prior approval. `--resume-task-id` only polls an existing task and does not create a duplicate paid request.

## Provider Failure Classification

| Provider message | Meaning | Required action |
|---|---|---|
| `PROVIDER_MODERATION_ERROR: TRADEMARK` | Output or supplied visual material triggered trademark moderation | Do not retry unchanged. Report the issue, return to storyboard prompt/image review, and obtain user approval before any compliant debranded or replacement asset is used. |
| Bare `PROVIDER_MODERATION_ERROR` | Moderation failed but the upstream subtype was omitted | Preserve and report the raw message. Do not infer that it is a trademark failure. Return to material review and seek the fuller provider reason when available. |
| `Read timed out`, `s3 upload failed`, `connection reset by peer` | Temporary upstream fetch failure for an input image | Keep the exact approved prompt and request; only resubmit after 用户明确确认. |
| `video_reference ... DURATION_TOO_LONG` | A stale request still supplied an overlong reference video | In this fixed-B skill, remove `reference_videos` and rebuild the preview. In another intentional video-reference workflow, cap the video at 15 seconds. |

Save the raw provider response plus the structured diagnosis to `failure.json`. Unknown failures are not automatically retried.

## Redacted cURL

```bash
curl -X POST "https://www.jimmyai.cn/api/open-api/v1/seedance/videos" \
  -H "Authorization: Bearer $JIMMYAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "seedance2.0-fast-md",
    "prompt": "Use @图片1 as storyboard ...",
    "duration": 15,
    "ratio": "9:16",
    "images": [
      "https://bucket.cos.ap-guangzhou.myqcloud.com/run/storyboard.png",
      "https://bucket.cos.ap-guangzhou.myqcloud.com/run/character-board.png",
      "https://bucket.cos.ap-guangzhou.myqcloud.com/run/product-board.png"
    ]
  }'
```
