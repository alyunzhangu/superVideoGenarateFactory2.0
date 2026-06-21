# Seedance V4 Upload Blocker

- Stage: COS publish before Seedance dry-run.
- Needed media: `outputs/route1_cut1_setup_v4/storyboards/segment_01_v4.png`.
- Reason: current environment cannot resolve the Tencent COS host.
- Error summary: `Failed to resolve 'veo-1304429692.cos.ap-guangzhou.myqcloud.com' ([Errno 8] nodename nor servname provided, or not known)`.
- Impact: v4 cannot yet receive a public HTTPS `@图片1` URL, so the final Seedance dry-run request hash cannot be generated honestly.
- Safe state: no Seedance paid task was created for v4.
- Retry after user switched session: still failed with the same DNS resolution error for `veo-1304429692.cos.ap-guangzhou.myqcloud.com`.
