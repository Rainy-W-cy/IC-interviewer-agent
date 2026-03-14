#!/usr/bin/env bash
set -euo pipefail

# 只需要修改下面四个变量中的前两个即可开始使用。
RESUME_PATH="./examples/resume.md"
REPO_PATH="./examples/candidate_repo"
SESSION_PATH="./sessions/demo.json"
REPORT_PATH="./out/interview_report.md"

PYTHON_BIN="./.venv/bin/python"

# 可选参数：不填则在 interview 阶段交互询问。
# NUM_QUESTIONS="10"
# MIX="architecture=3,implementation=4,hybrid=3"
NUM_QUESTIONS=""
MIX=""

mkdir -p "$(dirname "$SESSION_PATH")" "$(dirname "$REPORT_PATH")"

# 如果你没有项目仓库：
# 1. 可以直接把 REPO_PATH 留空：REPO_PATH=""
# 2. 也可以删除下面 analyze 命令中的 --repo "$REPO_PATH" 这一段
if [ -n "$REPO_PATH" ]; then
  "$PYTHON_BIN" -m ic_interviewer.cli analyze \
    --resume "$RESUME_PATH" \
    --repo "$REPO_PATH" \
    --session "$SESSION_PATH"
else
  "$PYTHON_BIN" -m ic_interviewer.cli analyze \
    --resume "$RESUME_PATH" \
    --session "$SESSION_PATH"
fi

"$PYTHON_BIN" -m ic_interviewer.cli inspect --session "$SESSION_PATH"

CMD=("$PYTHON_BIN" -m ic_interviewer.cli interview --session "$SESSION_PATH" --out "$REPORT_PATH")

if [ -n "$NUM_QUESTIONS" ]; then
  CMD+=(--num-questions "$NUM_QUESTIONS")
fi

if [ -n "$MIX" ]; then
  CMD+=(--mix "$MIX")
fi

"${CMD[@]}"
