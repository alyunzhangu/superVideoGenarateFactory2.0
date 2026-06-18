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


if __name__ == "__main__":
    unittest.main()
