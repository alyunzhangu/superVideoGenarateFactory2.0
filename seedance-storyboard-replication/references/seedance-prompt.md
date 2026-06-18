# Seedance Prompt Assembly

Build the final `seedance2.0-fast-md` prompt in this order.

## Source Of Truth

The approved 完整分镜脚本 is the execution source of truth. The reference video supplies motion, pacing, transition, and shooting-style reference. The storyboard supplies visual composition, identity, product, and scene reference.

The storyboard image is a visual reference; do not rely on text rendered inside the storyboard image. 不要依赖故事板图片中的文字，也不要要求 Seedance 自行识别图片里的完整脚本、口播或备注。Even when a reference video is uploaded, repeat the complete approved script as prompt text.

1. Actual image-number mapping:
   - `@图片1` is the approved storyboard overview.
   - `@图片2` is the optional character board.
   - `@图片3` is product board 1.
   - `@图片4` is optional product board 2.
2. Original reference-video mapping through `reference_videos`; describe it as the motion/rhythm/style reference.
3. Global product and character identity locks. Keep product shape, color, logo, packaging, material, scale, and use method consistent. Keep face, hairstyle, outfit, body proportion, and temperament consistent when a character board exists.
4. 完整分镜脚本, repeated Cut by Cut. Every Cut must include all of these fields:
   - `时间`: segment-local `00.0-02.5s` style timecode.
   - `脚本描述`: the complete visible scene, subject, action progression, and intended result.
   - `镜头`: shot size, angle, lens feeling, camera movement, and transition.
   - `人物与产品`: identity, pose/use action, product position, product fidelity, and continuity locks.
   - `口播内容`: exact spoken line, or explicitly `无口播`.
   - `备注`: environment/action sound, lighting, mood, speed, continuity, and Cut-local negative constraints.
5. Voiceover plus environment/action sound; no background music by default.
6. Global negative constraints: no subtitles, no screen text, no invented shots, no reordered Cuts, no product deformation, no identity drift.
7. Keep the whole prompt under 5000 characters with no unresolved image-number placeholders and no generic time placeholders. Compress repeated global wording before shortening any Cut's script facts. If the approved script cannot fit without losing facts, split on approved Cut boundaries instead of omitting them.

Never use vague substitutions such as “follow the storyboard,” “same as the reference,” or “continue similarly” in place of the Cut fields above.

## Four-Cut Example

Use `@图片1` as the storyboard visual reference, `@图片2` as the character board, `@图片3` as the product board, and `reference_videos[0]` as the rhythm and motion reference. Do not read instructions from text inside `@图片1`. Keep the exact person identity from `@图片2`. Keep the exact product appearance from `@图片3`: same color, shape, material, logo placement, packaging details, and real use method. Do not redraw or redesign the product.

Create a vertical 9:16 natural ecommerce experience video, realistic phone-shot style, soft indoor daylight, handheld but stable. No subtitles and no screen text.

Cut 1
- 时间: `00.0-03.0s`
- 脚本描述: At a kitchen counter, the user reaches into frame, takes the product from beside a cup, raises it to chest height, and turns its front toward camera.
- 镜头: Medium shot at counter height; stable handheld phone feeling; slight push-in following the hand; hard cut at the completed turn.
- 人物与产品: Match the face, hair, outfit, and body proportion from `@图片2`; product must match `@图片3` and remain unobstructed.
- 口播内容: “这个小东西我最近每天都会用。”
- 备注: Soft window daylight; light room tone and hand contact sound; no subtitles, no extra product, no deformed fingers.

Cut 2
- 时间: `03.0-06.5s`
- 脚本描述: The hand slowly rotates the product from front to side, pauses on the key texture, then tilts it so the material catches the light.
- 镜头: Tight close-up; small controlled arc movement; shallow depth of field; match cut from Cut 1 hand position.
- 人物与产品: Same hand, sleeve, product scale, color, material, and logo placement as Cut 1 and `@图片3`; no redesign.
- 口播内容: “主要是细节做得很扎实。”
- 备注: Subtle handling and material-friction sound; preserve left-to-right motion continuity; no screen text, no warped logo.

Cut 3
- 时间: `06.5-11.0s`
- 脚本描述: Over the user's shoulder, show the complete real use action: open the product, apply it to the intended area, finish the action, and set it beside the result.
- 镜头: Over-shoulder medium close-up; follow the hand with a small downward tilt; no missing action steps.
- 人物与产品: Same character identity and outfit from `@图片2`; exact product construction and real use method from `@图片3`.
- 口播内容: “用起来比我想的顺手很多。”
- 备注: Realistic use sound and small countertop movement; natural speed; no invented usage, no product-body intersection.

Cut 4
- 时间: `11.0-15.0s`
- 脚本描述: Present the clean final result with the product upright beside it; the user relaxes in the background while the product remains the visual anchor.
- 镜头: Clean result shot; hold steady for one second, then gently push in; end on a still product frame.
- 人物与产品: Maintain the same person, room direction, light direction, and exact product appearance from prior Cuts.
- 口播内容: “想要省事一点，可以直接试这个。”
- 备注: Natural room tone, no background music; no sales banner, subtitle, extra logo, extra character, or identity drift.

Negative: no subtitles, no floating text, no extra logo, no extra character, no invented scene, no reordered Cuts, no product shape change, no wrong color, no identity drift.
