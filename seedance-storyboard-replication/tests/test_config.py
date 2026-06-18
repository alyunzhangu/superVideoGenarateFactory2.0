from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from config import ConfigurationError, load_settings  # noqa: E402


class ConfigTest(unittest.TestCase):
    def test_loads_jimmy_and_tkagent_cos_aliases_from_one_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "seedance.env"
            env_file.write_text(
                "JIMMYAI_API_KEY=jimmy-secret\n"
                "TKAGENT_COS_BUCKET=seedance-temp-1300000000\n"
                "TKAGENT_COS_REGION=ap-guangzhou\n"
                "TKAGENT_COS_SECRET_ID=cos-id\n"
                "TKAGENT_COS_SECRET_KEY=cos-key\n",
                encoding="utf-8",
            )

            settings = load_settings(env_file, environ={})

        self.assertEqual(settings.cos_bucket, "seedance-temp-1300000000")
        self.assertEqual(settings.cos_region, "ap-guangzhou")
        self.assertEqual(
            settings.cos_public_base_url,
            "https://seedance-temp-1300000000.cos.ap-guangzhou.myqcloud.com",
        )
        self.assertNotIn("jimmy-secret", repr(settings))
        self.assertNotIn("cos-key", repr(settings))

    def test_require_cos_names_missing_variables_without_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "seedance.env"
            env_file.write_text("JIMMYAI_API_KEY=set\n", encoding="utf-8")
            settings = load_settings(env_file, environ={})

        with self.assertRaisesRegex(ConfigurationError, "TENCENT_COS_BUCKET"):
            settings.require_cos()

    def test_environment_values_override_file_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "seedance.env"
            env_file.write_text(
                "JIMMYAI_API_KEY=file-key\n"
                "TENCENT_COS_BUCKET=file-bucket\n"
                "TENCENT_COS_REGION=ap-guangzhou\n"
                "TENCENT_COS_SECRET_ID=file-id\n"
                "TENCENT_COS_SECRET_KEY=file-secret\n",
                encoding="utf-8",
            )
            settings = load_settings(
                env_file,
                environ={
                    "JIMMYAI_API_KEY": "env-key",
                    "TENCENT_COS_BUCKET": "env-bucket",
                },
            )

        self.assertEqual(settings.jimmy_api_key, "env-key")
        self.assertEqual(settings.cos_bucket, "env-bucket")
        self.assertEqual(
            settings.cos_public_base_url,
            "https://env-bucket.cos.ap-guangzhou.myqcloud.com",
        )

    def test_example_env_lists_variables_without_values(self) -> None:
        example = (
            Path(__file__).resolve().parents[1]
            / "references"
            / "seedance.env.example"
        )
        for raw_line in example.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            self.assertRegex(line, r"^[A-Z0-9_]+=$")


if __name__ == "__main__":
    unittest.main()
