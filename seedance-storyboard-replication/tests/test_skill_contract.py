from pathlib import Path
import unittest


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
        frontmatter = skill_text.split("---", 2)[1]

        self.assertIn("name: seedance-storyboard-replication", skill_text)
        self.assertRegex(frontmatter, r"(?m)^description: .*Use when")
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertTrue((SKILL_ROOT / "references").is_dir())
        self.assertTrue((SKILL_ROOT / "scripts").is_dir())


if __name__ == "__main__":
    unittest.main()
