import re
import unittest
from pathlib import Path


CONTAINER = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    CONTAINER
    if CONTAINER.name == "seedance-storyboard-replication"
    else CONTAINER / "seedance-storyboard-replication"
)


def parse_frontmatter(skill_text):
    match = re.match(r"\A---\s*\n(?P<body>.*?)\n---(?:\s*\n|\Z)", skill_text, re.DOTALL)
    if match is None:
        raise ValueError("SKILL.md is missing YAML frontmatter")
    return dict(
        re.findall(r"(?m)^([a-z_]+):\s*(.*?)\s*$", match.group("body"))
    )


def parse_interface(openai_text):
    match = re.search(
        r"(?m)^interface:\s*\n(?P<body>(?:  [^\n]*\n?)*)", openai_text
    )
    if match is None:
        raise ValueError("openai.yaml is missing interface metadata")
    return dict(
        re.findall(r'(?m)^  ([a-z_]+):\s*"([^"]*)"\s*$', match.group("body"))
    )


class SkillContractTest(unittest.TestCase):
    def test_skill_scaffold_contract(self):
        self.assertTrue(SKILL_ROOT.is_dir(), f"missing skill scaffold: {SKILL_ROOT}")

        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(skill_text)

        self.assertEqual(frontmatter["name"], "seedance-storyboard-replication")
        self.assertIn("Use when", frontmatter["description"])

        openai_yaml = SKILL_ROOT / "agents" / "openai.yaml"
        self.assertTrue(openai_yaml.is_file())
        interface = parse_interface(openai_yaml.read_text(encoding="utf-8"))

        self.assertEqual(interface["display_name"], "Seedance Storyboard Replication")
        self.assertGreaterEqual(len(interface["short_description"]), 25)
        self.assertLessEqual(len(interface["short_description"]), 64)
        self.assertIn(
            "$seedance-storyboard-replication", interface["default_prompt"]
        )
        self.assertTrue((SKILL_ROOT / "references").is_dir())
        self.assertTrue((SKILL_ROOT / "scripts").is_dir())

    def test_skill_declares_both_routes_and_approval_gates(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "路线一：已有分镜脚本",
            "路线二：仅提供参考视频",
            "不要二次确认分镜脚本",
            "确认反解分镜脚本",
            "确认故事板",
            "image2",
            "16:9 横版电影制作板",
            "固定 B 方案",
            "参考视频仅用于反解分镜、节奏分析和故事板生成",
            "禁止上传参考视频到 COS",
            "禁止发送 `reference_videos`",
            "最多 4 张",
            "不默认添加背景音乐",
            "确认 Seedance 提示词",
            "approval_preview.json",
            "请求摘要哈希",
            "任何提示词或请求参数变化都会使旧确认失效",
        ):
            self.assertIn(required, text)

    def test_both_routes_stop_for_exact_seedance_prompt_approval(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Route 1", text)
        self.assertIn("Route 2", text)
        self.assertGreaterEqual(text.count("确认 Seedance 提示词"), 3)
        self.assertIn("完整 Seedance 提示词", text)
        self.assertIn("图片映射", text)
        self.assertIn("时长和分段计划", text)
        self.assertIn("不得调用 Seedance", text)

    def test_skill_limits_reference_video_to_two_story_driven_boards(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "参考视频最长 30 秒",
            "15 秒以内最稳定",
            "18-30 秒",
            "最多两张故事板",
            "剧情切点",
            "禁止为了均衡时长自动选择",
            "continuity_manifest.json",
            "segment_01",
            "segment_02",
            "当前分段故事板",
        ):
            self.assertIn(required, text)

    def test_required_references_exist(self):
        for name in (
            "fukeGem.md",
            "daohuo_storyboard_prompt.md",
            "seedance-prompt.md",
            "jimmyai-api.md",
            "seedance.env.example",
        ):
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_storyboard_prompt_requires_production_board_layout(self):
        text = (SKILL_ROOT / "references" / "daohuo_storyboard_prompt.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "16:9",
            "导演预制作指南",
            "共享创意指导",
            "角色与风格参考",
            "人物多角度",
            "人物细节特写",
            "产品参考区",
            "环境和场景设计",
            "俯视动线示意图",
            "故事板分镜区",
            "灯光/情绪/风格备注",
            "情绪和关键词块",
            "音频/音调部分",
            "电影摄影笔记",
            "重要事项",
            "分镜图只保留",
            "不要在故事板图片中排版完整分镜脚本",
            "不要依赖故事板图片中的文字",
        ):
            self.assertIn(required, text)

    def test_storyboard_prompt_uses_fixed_skeleton_with_dynamic_fields(self):
        prompt_text = (
            SKILL_ROOT / "references" / "daohuo_storyboard_prompt.md"
        ).read_text(encoding="utf-8")
        for required in (
            "固定骨架",
            "动态填充",
            "{{VIDEO_TITLE}}",
            "{{DURATION}}",
            "{{SHOT_COUNT}}",
            "{{CHARACTER_REFERENCE_ROLE}}",
            "{{PRODUCT_REFERENCE_ROLE}}",
            "{{REFERENCE_VIDEO_ROLE}}",
            "{{SHOT_CARDS}}",
            "{{EXACT_LABELS}}",
            "{{TRADEMARK_SAFETY_NOTE}}",
            "{{SEGMENT_INDEX}}",
            "{{SEGMENT_DURATION}}",
            "{{GLOBAL_CUT_RANGE}}",
            "{{INCOMING_CONTINUITY}}",
            "{{OUTGOING_CONTINUITY}}",
            "{{ADJACENT_BOARD_ROLE}}",
            "{{CONTINUITY_MANIFEST}}",
            "不得保留未替换占位符",
        ):
            self.assertIn(required, prompt_text)

        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("固定骨架 + 动态填充", skill_text)
        self.assertIn("only storyboard prompt source", skill_text)

    def test_seedance_prompt_carries_script_text_not_storyboard_text(self):
        text = (SKILL_ROOT / "references" / "seedance-prompt.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "完整分镜脚本",
            "脚本描述",
            "口播内容",
            "备注",
            "不要依赖故事板图片中的文字",
            "The storyboard image is a visual reference",
            "禁止发送 `reference_videos`",
        ):
            self.assertIn(required, text)
        self.assertNotIn("reference_videos[0]", text)

    def test_jimmy_api_reference_locks_b_route_without_reference_video(self):
        text = (SKILL_ROOT / "references" / "jimmyai-api.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("固定 B 方案", text)
        self.assertIn("不要发送 `reference_videos`", text)
        self.assertNotIn('"reference_videos": [', text)

    def test_skill_classifies_known_provider_failures(self):
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        api_text = (SKILL_ROOT / "references" / "jimmyai-api.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "PROVIDER_MODERATION_ERROR: TRADEMARK",
            "Read timed out",
            "s3 upload failed",
            "DURATION_TOO_LONG",
            "用户明确确认",
        ):
            self.assertIn(required, skill_text + api_text)

    def test_skill_separates_visual_board_from_seedance_script(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "故事板图片只承载视觉参考和重要事项",
            "完整分镜脚本必须作为文本写入 Seedance prompt",
            "不要让 Seedance 从故事板图片中识别完整脚本",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
