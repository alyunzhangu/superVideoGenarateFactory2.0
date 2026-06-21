#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="seedance-storyboard-replication"
SOURCE_DIR="$ROOT_DIR/$SKILL_NAME"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
TARGET_DIR="$CODEX_HOME_DIR/skills/$SKILL_NAME"
VALIDATOR="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"

require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "MISSING $name"
    exit 1
  fi
}

require_command python3
require_command ffmpeg
require_command ffprobe

if ! python3 -c 'import qcloud_cos' >/dev/null 2>&1; then
  echo "MISSING qcloud_cos"
  echo "Run: python3 -m pip install -r $ROOT_DIR/requirements.txt"
fi

if [ ! -d "$SOURCE_DIR" ]; then
  echo "MISSING $SOURCE_DIR"
  exit 1
fi

mkdir -p "$(dirname "$TARGET_DIR")"
rm -rf "$TARGET_DIR"
cp -R "$SOURCE_DIR" "$TARGET_DIR"

find "$TARGET_DIR" -name '*.env' ! -name '*.env.example' -print -quit | while read -r env_file; do
  echo "INVALID copied real env file: $env_file"
  exit 1
done

if [ -f "$VALIDATOR" ]; then
  python3 "$VALIDATOR" "$TARGET_DIR"
fi

echo "READY installed $SKILL_NAME at $TARGET_DIR"
