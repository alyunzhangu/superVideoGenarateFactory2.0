# Seedance QC Report — Storage Bag Replication

## Files

- Result video: `outputs/seedance/segment_01/result.mp4`
- Storyboard: `outputs/storyboards/segment_01_v1.png`
- Prompt: `outputs/seedance_prompt_segment_01.md`
- Task ID: `videos_21e415f719eb4f63a9e943edee71168e`
- Request SHA256: `55382541f0fe0005be7d77bb3f0349c1322bb0c08c7d746e392c9505003a0afb`

## Technical probe

- Container has video stream: yes
- Video: H.264, 720×1280, 24 fps
- Audio stream: yes
- Audio: AAC, 44.1 kHz, stereo
- Duration: 12.05 seconds
- Audio loudness probe: mean -26.4 dB, max -3.1 dB

## Visual QC

- Cut order: broadly preserved from closet opening → clothing mess → demonstrator seated → product reveal → packing → zip/closed reveal.
- Character identity: pass. The primary woman stays close to the character board: beige hijab, cream cardigan, peach top, light trousers.
- Product fidelity: pass. The storage bag remains an opaque gray-white striped soft storage bag with dark trim, front handles, double top zipper, and realistic scale.
- Product physics: pass. The bag opens, receives folded clothes, and closes without becoming a transparent frame box.
- Audio: pass at stream level. The output includes an audio track.
- Notable deviation: the opening chaos is softened. Instead of a strong clothing avalanche and the demonstrator sliding out from the pile, the generated video appears closer to the demonstrator stepping/climbing out from the wardrobe area before sitting. This is a reference-motion drift, not a product-fidelity failure.

## Verdict

Usable first pass if the priority is product fidelity and clean storage-bag demonstration. If the priority is closer viral-comedy replication of the reference Hook, regenerate with stronger constraints on Cut 2-3: heavier clothing avalanche, no standing/climbing pose, demonstrator must fall/slide out onto the pile before sitting up.
