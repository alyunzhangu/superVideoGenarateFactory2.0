# 故事板提示词：固定骨架 + 动态填充

这是 Skill 唯一的故事板生图模板。它不保存某个具体商品、人物或案例，而是固定成功验证过的 16:9 导演预制作指南结构；每次任务根据用户素材和已确认分镜动态填充。

## 使用原则

- **固定骨架**：版式、素材职责、人物与产品一致性、短标签格式、文字限制、Negative Prompt。
- **动态填充**：视频标题、时长、镜头数、人物描述、产品锁定项、参考视频用途、逐 Cut 画面和精确标签。
- `@分镜脚本` 是镜头顺序、时间、动作和情绪的唯一来源，不得改剧情、重排 Cut 或增加无关镜头。
- 故事板图片只负责视觉确认。完整分镜脚本、口播和备注必须在提交 Seedance 时作为文本逐 Cut 传入。
- 生成前替换全部 `{{...}}` 字段；最终发送给 image2 的提示词不得保留未替换占位符。

## 动态字段

每次生成故事板前，根据当前任务填充：

| 字段 | 内容 |
|---|---|
| `{{VIDEO_TITLE}}` | 产品或视频主题的短标题 |
| `{{DURATION}}` | 视频总时长 |
| `{{SHOT_COUNT}}` | 已确认的 Cut 数量 |
| `{{TARGET_VIDEO_RATIO}}` | 成片比例，默认 9:16 |
| `{{CHARACTER_REFERENCE_ROLE}}` | 人物参考图编号、身份、脸、发型/头巾、服装和体型锁定项；无人设图时写明手部或纯产品策略 |
| `{{PRODUCT_REFERENCE_ROLE}}` | 产品参考图编号、品类、形状、颜色、材质、图案、logo、结构和比例锁定项 |
| `{{REFERENCE_VIDEO_ROLE}}` | 参考视频或关键帧板编号，以及只允许参考的节奏、运镜、构图和场景推进 |
| `{{VISUAL_STYLE}}` | 实拍风格、光线、质感和摄影语言 |
| `{{COLOR_PALETTE}}` | 主色板 |
| `{{ENVIRONMENT_PLAN}}` | 主要室内/户外环境、连续性和动线 |
| `{{SHOT_CARDS}}` | 按已确认顺序生成的全部 Cut 卡片 |
| `{{EXACT_LABELS}}` | 卡片与底栏允许出现的全部精确短文字 |
| `{{AUDIO_NOTE}}` | 口播/环境声方向；默认不添加背景音乐 |
| `{{TASK_NEGATIVES}}` | 当前人物、产品和场景特有的禁止项 |

## 动态组装步骤

1. 明确每份输入素材的唯一职责。人物图只锁身份与造型，产品图只锁产品，参考视频只锁节奏、运镜、构图和场景推进。
2. 将已确认分镜逐 Cut 转成 `{{SHOT_CARDS}}`，镜头数量必须等于 `{{SHOT_COUNT}}`。
3. 每个 Cut 从完整脚本提炼一个关键动作和一个必要约束，生成短标签并汇总为 `{{EXACT_LABELS}}`。
4. 默认使用简短大写英文标签降低小字变形风险；用户明确要求其他语言时才切换。
5. 检查人物、产品、场景和光线连续性，删除与本任务无关的通用描述。
6. 替换全部占位符后再调用 image2。不要把本文件连同未填字段原样提交。

## 固定版式

最终输出是一张专业、电影化、网格清晰的 `16:9` 横版电影制作板，而不是普通九宫格或竖屏截图拼图。

必须包含：

1. **共享创意指导**：顶部栏显示标题、`{{SHOT_COUNT}}`、`{{TARGET_VIDEO_RATIO}}`、统一调色板和拍摄方式。
2. **角色与风格参考**：有人物图时展示人物多角度，包括正面、侧面、背面或四分之三侧面。
3. **人物细节特写**：脸部/眼部、手部、头发或头巾、服装材质和关键配饰。
4. **产品参考区**：产品正面、材质/logo 微距、关键结构、开口/内部或使用部件。
5. **环境和场景设计**：主要环境氛围，以及简洁的俯视动线示意图，标出摄像机位置、人物方向和产品位置。
6. **故事板分镜区**：按 Cut 顺序展示全部镜头，分镜图只保留 Cut、时间、重要事项和必要约束。
7. **灯光/情绪/风格备注**：使用色块、光线图标和短标签表达。
8. **情绪和关键词块**：只使用少量关键词。
9. **音频/音调部分**：口播、环境/动作声和是否有音乐。
10. **电影摄影笔记**：用短标签表示镜头特性、运动风格和后期感觉。

不要在故事板图片中排版完整分镜脚本、长段口播或密集备注。不要依赖故事板图片中的文字向 Seedance 传递剧情。

## Cut 卡片格式

每个 Cut 卡片必须包含一张主画面和一条干净说明条：

```text
Cut {{CUT_NUMBER}}
画面：{{COMPLETE_VISUAL_DESCRIPTION_FOR_IMAGE_GENERATION}}
标签："{{NN}}  {{START}}-{{END}}  {{KEY_ACTION_TAG}} · {{IDENTITY_OR_PRODUCT_LOCK_TAG}}"
```

标签只表达重要事项：

- `{{KEY_ACTION_TAG}}`：当前镜头唯一关键动作，例如 `SEARCH`、`REVEAL`、`TEXTURE`、`COMPARE`。
- `{{IDENTITY_OR_PRODUCT_LOCK_TAG}}`：最容易漂移的一项，例如 `KEEP FACE`、`SAME PRODUCT`、`LOGO LOCK`、`TRUE SCALE`。
- 标签必须短、粗、清晰；不放口播，不放完整脚本，不放声音细节。

## 可提交给 image2 的固定提示词骨架

```text
Use case: infographic-diagram
Asset type: 16:9 cinematic pre-production storyboard / visual planning board for a {{DURATION}} vertical ecommerce UGC video.

Input roles:
- Character reference: {{CHARACTER_REFERENCE_ROLE}}
- Product reference: {{PRODUCT_REFERENCE_ROLE}}
- Reference video or contact sheet: {{REFERENCE_VIDEO_ROLE}}

Primary request:
Create one polished landscape 16:9 director's production board for a {{TARGET_VIDEO_RATIO}} ecommerce video titled "{{VIDEO_TITLE}}". Use a professional modular grid, clear hierarchy, generous spacing, and realistic commercial pre-production design. This must feel like a director's visual guide, not a plain nine-grid.

Fixed layout:
- Top: shared creative direction with title, {{SHOT_COUNT}} shots, target ratio, palette, environment, and camera style.
- Left: CHARACTER section with character/style reference, multiple angles, face/eye, hand, clothing or accessory details.
- Center: STORYBOARD section containing exactly {{SHOT_COUNT}} ordered Cut cards.
- Right: PRODUCT section with front view, texture/logo macro, structural detail, interior/use detail, and a simple top-down camera movement diagram.
- Bottom: large short labels for lighting, camera, palette, audio/tone, mood keywords, and cinematography notes.

Environment and movement:
{{ENVIRONMENT_PLAN}}

Storyboard cards:
{{SHOT_CARDS}}

Visual style:
{{VISUAL_STYLE}}
Color palette: {{COLOR_PALETTE}}
Audio direction: {{AUDIO_NOTE}}

Exact allowed text:
{{EXACT_LABELS}}

Identity and product locks:
Preserve the character identity, face, styling, outfit, body proportion, and hands defined by the character reference. Preserve the exact product category, silhouette, dimensions, color, material, pattern, logo placement, construction, parts, scale, and real use method defined by the product reference. Do not copy people, subtitles, branding, or screen text from the reference video.

Text constraints:
Render only the exact allowed text. Use large crisp high-contrast sans-serif type on clean solid caption strips. No paragraphs, no dialogue, no complete script, no tiny filler text. If optional text cannot be rendered accurately, leave the area blank instead of inventing characters.

Avoid:
garbled text, pseudo-writing, dense paragraphs, subtitles inside scene images, watermark, extra storyboard panels, reordered shots, identity drift, changed face, changed hairstyle or outfit, extra people, malformed hands, extra fingers, product deformation, wrong product category, changed color, changed pattern, fake logo, duplicate product, floating product, unrelated props, random scene changes, anime, illustration, plastic skin, hard-sell poster, shopping banner, {{TASK_NEGATIVES}}.
```

## 提交前检查

- `{{SHOT_CARDS}}` 中 Cut 数量与已确认脚本一致。
- 所有镜头顺序、时间和动作均来自已确认脚本。
- 人物、产品和参考视频职责没有混用。
- `{{EXACT_LABELS}}` 只包含短标签，没有完整分镜脚本或口播。
- 所有 `{{...}}` 已替换，提示词中没有占位符残留。
- 故事板图片比例为 16:9，成片目标比例单独写明。
- 产品 fidelity 优先于视觉新奇，人物一致性优先于姿势变化。
- 默认只规划口播、环境声和动作声，不默认添加背景音乐。
