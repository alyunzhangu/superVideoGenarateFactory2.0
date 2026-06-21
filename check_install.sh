#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="seedance-storyboard-replication"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILL_DIR="$CODEX_HOME_DIR/skills/$SKILL_NAME"
SECRET_FILE="$HOME/.codex/secrets/seedance.env"

report() {
  local state="$1"
  local name="$2"
  echo "$state $name"
}

if [ -f "$SKILL_DIR/SKILL.md" ]; then
  report READY "installed SKILL.md"
else
  report MISSING "installed SKILL.md"
fi

if [ -f "$SECRET_FILE" ]; then
  mode="$(python3 - "$SECRET_FILE" <<'PY'
from pathlib import Path
import stat
import sys
print(oct(stat.S_IMODE(Path(sys.argv[1]).stat().st_mode))[2:].zfill(3))
PY
)"
  if [ "$mode" = "600" ]; then
    report READY "secret file mode 600"
  else
    report INVALID "secret file mode 600"
  fi
else
  report MISSING "secret file mode 600"
fi

python3 - "$SECRET_FILE" <<'PY'
from pathlib import Path
import sys

secret_file = Path(sys.argv[1])
values = {}
if secret_file.exists():
    for raw in secret_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")

def has(primary, alias=""):
    return bool(values.get(primary) or (alias and values.get(alias)))

checks = [
    ("JIMMYAI_API_KEY", has("JIMMYAI_API_KEY")),
    ("COS bucket", has("TENCENT_COS_BUCKET", "TKAGENT_COS_BUCKET")),
    ("COS region", has("TENCENT_COS_REGION", "TKAGENT_COS_REGION")),
    ("COS SecretId", has("TENCENT_COS_SECRET_ID", "TKAGENT_COS_SECRET_ID")),
    ("COS SecretKey", has("TENCENT_COS_SECRET_KEY", "TKAGENT_COS_SECRET_KEY")),
]
for name, ok in checks:
    print(("READY" if ok else "MISSING") + " " + name)
PY

if python3 -c 'import qcloud_cos' >/dev/null 2>&1; then
  report READY "qcloud_cos"
else
  report MISSING "qcloud_cos"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  report READY "ffmpeg"
else
  report MISSING "ffmpeg"
fi

if command -v ffprobe >/dev/null 2>&1; then
  report READY "ffprobe"
else
  report MISSING "ffprobe"
fi
