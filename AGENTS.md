# AGENTS.md

## 默认维护规则

1. 修改 CLI 参数时，必须同步更新：
- `README.md`
- `run_analyze.sh`
- `run_interview.sh`
- `run_all.sh`

2. 修改面试流程时，必须优先保证以下一致性：
- 终端交互文案
- `session.json` 写回行为
- Markdown 报告内容
- 测试断言

3. 新增用户可见参数时：
- 优先保持中文说明清晰
- README 中的命令必须与真实 CLI 参数完全一致
- 如果参数仅支持交互、不支持命令行显式传入，必须在 README 中写清楚

4. 修改报告内容时：
- 尽量保持“点评 / 参考标准答案 / 面试背诵版”三部分风格统一
- 中文和英文输出必须整链路一致

5. 任何改动完成后，默认执行：
```bash
./.venv/bin/pytest -q
./.venv/bin/python -m ic_interviewer.cli --help
```
