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
- Reference videos: put the original reference video COS URL in `reference_videos`.
- Reference audio: do not send uploaded reference audio; no `reference_audios` field.
- Media URLs: must be anonymous public HTTPS URLs, typically Tencent COS object URLs.
- Statuses: `queued`, `processing`, `completed`, `failed`.
- Result video URL path: `data.result.video_url`.
- Result retention: download promptly; JimmyAI result links are documented as retained for about three days.

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
      "https://bucket.cos.ap-guangzhou.myqcloud.com/run/product-board.png"
    ],
    "reference_videos": [
      "https://bucket.cos.ap-guangzhou.myqcloud.com/run/reference.mp4"
    ]
  }'
```
