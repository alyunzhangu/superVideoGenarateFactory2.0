# Route 1 Seedance Preview Resume Status

## Status

Resolved on 2026-06-20: COS publishing now works, all four approved image references were re-uploaded, and the Segment 1/1 Seedance dry-run approval preview was generated.

After user approval of the dry-run request hash, a paid task creation attempt was made on 2026-06-20. JimmyAI did not return a `task_id`; the raw provider message was `系统繁忙，请稍后重试`. The failure was saved to `failure.json`. Per the workflow rules for unknown provider failures, do not automatically resubmit without a fresh user confirmation.

The user then explicitly confirmed an exact retry. The same request hash and same four COS image URLs were submitted again on 2026-06-20, and JimmyAI again returned `系统繁忙，请稍后重试` without a `task_id`. No `result.mp4` was created.

## Previous Blocker

COS upload failed because the current environment could not resolve the public COS host:

`veo-1304429692.cos.ap-guangzhou.myqcloud.com`

Retried after user request; the retry failed with the same DNS / name resolution error:

`Failed to resolve 'veo-1304429692.cos.ap-guangzhou.myqcloud.com' ([Errno 8] nodename nor servname provided, or not known)`

Retried again on 2026-06-20. The current Codex terminal environment failed DNS resolution for COS and unrelated public domains (`www.baidu.com`, `www.qq.com`) in the same check, confirming the blocker is the execution environment's DNS/network access rather than the COS credentials or media files.

The failing step was publishing these four approved image references:

1. `outputs/route1_corrected/storyboards/segment_01_v1.png`
2. `/Users/jiangyongjian/Downloads/character.png`
3. `/Users/jiangyongjian/Downloads/ChatGPT Image 2026年6月2日 21_44_17.png`
4. `/Users/jiangyongjian/Downloads/ChatGPT Image 2026年6月19日 21_55_31.png`

## Resume Result

- New COS manifest: `outputs/route1_corrected/seedance/segment_01/published_media.json`
- Dry-run request: `outputs/route1_corrected/seedance/segment_01/request.redacted.json`
- Approval preview: `outputs/route1_corrected/seedance/segment_01/approval_preview.json`
- Request SHA256: `9c204a251a20fbc4670cbbfae9a09a663d2049ebc862c7795893e3b4a6c4f114`
- Request check: `model=seedance2.0-fast-md`, `duration=12`, `ratio=9:16`, `images=4`, no `reference_videos`.

## Next Step

The prompt, image URLs, and request hash remain unchanged. Since two create attempts have now hit the same provider-busy response, wait before retrying again or check JimmyAI service/account status. Resubmit with the same `--approved-request-sha256` only after explicit user confirmation.
