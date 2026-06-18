from pathlib import Path
import unittest

import yaml


CONTAINER = Path(__file__).resolve().parents[1]
SKILL_ROOT = (
    CONTAINER
    if CONTAINER.name == "seedance-storyboard-replication"
    else CONTAINER / "seedance-storyboard-replication"
)


class SkillContractTest(unittest.TestCase):
    def test_skill_scaffold_contract(self):
        self.assertTrue(SKILL_ROOT.is_dir(), f"missing skill scaffold: {SKILL_ROOT}")

        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(skill_text.split("---", 2)[1])

        self.assertEqual(frontmatter["name"], "seedance-storyboard-replication")
        self.assertIn("Use when", frontmatter["description"])

        openai_yaml = SKILL_ROOT / "agents" / "openai.yaml"
        self.assertTrue(openai_yaml.is_file())
        interface = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))["interface"]

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
