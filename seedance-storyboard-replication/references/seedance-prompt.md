# Seedance Prompt Assembly

Build the final `seedance2.0-fast-md` prompt in this order.

1. Actual image-number mapping:
   - `@图片1` is the approved storyboard overview.
   - `@图片2` is the optional character board.
   - `@图片3` is product board 1.
   - `@图片4` is optional product board 2.
2. Original reference-video mapping through `reference_videos`; describe it as the motion/rhythm/style reference.
3. Global product and character identity locks. Keep product shape, color, logo, packaging, material, scale, and use method consistent. Keep face, hairstyle, outfit, body proportion, and temperament consistent when a character board exists.
4. Segment-local Cut timecodes plus concrete camera/action direction. Use `00.0-02.5s` style local time, not global placeholders.
5. Voiceover plus environment/action sound; no background music by default.
6. Negative constraints: no subtitles, no screen text, no invented shots, no reordered Cuts, no product deformation, no identity drift.
7. Keep the whole prompt under 5000 characters with no unresolved image-number placeholders and no generic time placeholders.

## Four-Cut Example

Use `@图片1` as the storyboard, `@图片2` as the product board, and `reference_videos[0]` as the rhythm and motion reference. Keep the exact product appearance from `@图片2`: same color, shape, material, logo placement, packaging details, and real use method. Do not redraw or redesign the product.

Create a vertical 9:16 natural ecommerce experience video, realistic phone-shot style, soft indoor daylight, handheld but stable. No subtitles and no screen text.

Cut 1 `00.0-03.0s`: medium shot from the kitchen counter, user reaches into frame and picks up the product shown in `@图片2`; camera makes a slight push-in following the hand. Voiceover: "这个小东西我最近每天都会用。" Sound: light room tone and hand contact with packaging.

Cut 2 `03.0-06.5s`: close-up of the product in hand, rotate slowly to show front, side, and key texture. Keep the product pixels faithful to `@图片2`; no deformation. Voiceover: "主要是细节做得很扎实。" Sound: subtle handling and packaging friction.

Cut 3 `06.5-11.0s`: over-shoulder usage shot, user applies the product exactly as the storyboard in `@图片1` shows; camera follows the action with a small downward tilt. Voiceover: "用起来比我想的顺手很多。" Sound: realistic use sound and small countertop movement.

Cut 4 `11.0-15.0s`: clean final result shot, product stays visible beside the result, camera holds steady for one second then gently pushes in. Voiceover: "想要省事一点，可以直接试这个。" Sound: natural room tone, no background music.

Negative: no subtitles, no floating text, no extra logo, no extra character, no invented scene, no reordered Cuts, no product shape change, no wrong color, no identity drift.
