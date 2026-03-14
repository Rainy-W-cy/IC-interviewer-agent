#!/usr/bin/env bash
set -euo pipefail

# 常用情况下，只需要确认 SESSION_PATH 和 REPORT_PATH 即可。
# 如果你想统一放在自己的路径里，也可以一并修改 RESUME_PATH / REPO_PATH。
RESUME_PATH="./examples/resume.md"
REPO_PATH="./examples/candidate_repo"
SESSION_PATH="./sessions/demo.json"
REPORT_PATH="./out/interview_report.md"

PYTHON_BIN="./.venv/bin/python"

mkdir -p "$(dirname "$SESSION_PATH")" "$(dirname "$REPORT_PATH")"

# 可选参数：
# NUM_QUESTIONS="10"
# MIX="architecture=3,implementation=4,hybrid=3"
NUM_QUESTIONS=""
MIX=""

CMD=("$PYTHON_BIN" -m ic_interviewer.cli interview --session "$SESSION_PATH" --out "$REPORT_PATH")

if [ -n "$NUM_QUESTIONS" ]; then
  CMD+=(--num-questions "$NUM_QUESTIONS")
fi

if [ -n "$MIX" ]; then
  CMD+=(--mix "$MIX")
fi

"${CMD[@]}"
