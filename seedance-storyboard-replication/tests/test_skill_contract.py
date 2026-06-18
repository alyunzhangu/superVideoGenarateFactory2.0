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
            "reference_videos",
            "最多 4 张",
            "不默认添加背景音乐",
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
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
