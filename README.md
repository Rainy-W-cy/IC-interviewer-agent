# 集成电路模拟面试 CLI 工具

这是一个用于集成电路岗位模拟面试的本地命令行工具。它可以读取候选人简历和项目仓库，自动生成面试题、收集回答、给出点评，并导出 Markdown 面试报告。

## 项目简介

当前工具支持以下核心流程：

- 读取简历并生成 `session.json`
- 可选扫描项目仓库并建立最小索引
- 自动生成架构类 / 实现类 / 混合类面试题
- 交互式收集回答并即时写回会话文件
- 输出中文或英文面试报告

## 环境准备

建议先在项目根目录使用虚拟环境中的 Python：

```bash
./.venv/bin/python -m ic_interviewer.cli --help
```

如果你还没有准备好环境，至少需要确保：

- 当前目录是项目根目录
- `.venv` 已可用
- 简历文件路径正确
- 如果要分析代码仓库，项目仓库路径正确

## 用户只需要修改这两个位置

对于大多数用户，只需要修改下面两个路径即可开始：

- 简历路径：`RESUME_PATH`
- 项目仓库路径：`REPO_PATH`

这两个变量已经写在以下脚本中：

- [run_analyze.sh](/home/yian/ic-interviewer/run_analyze.sh)
- [run_interview.sh](/home/yian/ic-interviewer/run_interview.sh)
- [run_all.sh](/home/yian/ic-interviewer/run_all.sh)

默认示例值：

- `RESUME_PATH="./examples/resume.md"`
- `REPO_PATH="./examples/candidate_repo"`

如果你没有项目仓库：

- 在脚本里把 `REPO_PATH` 改成空字符串：`REPO_PATH=""`
- 或者删除命令中的 `--repo "$REPO_PATH"`

## 方式 A：先分析，再面试

### 第一步：修改路径

打开 [run_analyze.sh](/home/yian/ic-interviewer/run_analyze.sh) 和 [run_interview.sh](/home/yian/ic-interviewer/run_interview.sh)，至少修改：

- `RESUME_PATH`
- `REPO_PATH`

常用输出路径变量也已经准备好：

- `SESSION_PATH`
- `REPORT_PATH`

### 第二步：先分析

```bash
./run_analyze.sh
```

这个脚本内部实际调用的是当前真实 CLI 参数：

```bash
./.venv/bin/python -m ic_interviewer.cli analyze \
  --resume "$RESUME_PATH" \
  --repo "$REPO_PATH" \
  --session "$SESSION_PATH"
```

如果没有项目仓库，则会改为：

```bash
./.venv/bin/python -m ic_interviewer.cli analyze \
  --resume "$RESUME_PATH" \
  --session "$SESSION_PATH"
```

### 第三步：开始面试

```bash
./run_interview.sh
```

这个脚本内部实际调用的是：

```bash
./.venv/bin/python -m ic_interviewer.cli interview \
  --session "$SESSION_PATH" \
  --out "$REPORT_PATH"
```

你也可以在脚本中额外设置：

- `NUM_QUESTIONS`
- `MIX`

例如：

```bash
NUM_QUESTIONS="10"
MIX="architecture=3,implementation=4,hybrid=3"
```

如果不设置这些参数，系统会在终端里交互询问：

- 面试语言（中文/英文，默认中文）
- 题目数量
- 是否自定义题型分布
- 是否开始本次模拟面试

## 方式 B：一键运行

如果你希望从分析直接进入面试，可以使用：

```bash
./run_all.sh
```

这个脚本会顺序执行：

1. `analyze`
2. `inspect`
3. `interview`

对于第一次体验，这是最省事的方式。

同样地，如果没有项目仓库：

- 把 `REPO_PATH` 设为空
- 或删除 analyze 命令中的 `--repo "$REPO_PATH"`

## 手动命令方式

如果你不想使用脚本，也可以直接手动调用 CLI。

### 1. 分析简历和项目仓库

```bash
./.venv/bin/python -m ic_interviewer.cli analyze \
  --resume ./examples/resume.md \
  --repo ./examples/candidate_repo \
  --session ./sessions/demo.json
```

如果没有项目仓库：

```bash
./.venv/bin/python -m ic_interviewer.cli analyze \
  --resume ./examples/resume.md \
  --session ./sessions/demo.json
```

### 2. 查看分析结果

```bash
./.venv/bin/python -m ic_interviewer.cli inspect \
  --session ./sessions/demo.json
```

### 3. 手动确认分析结果

```bash
./.venv/bin/python -m ic_interviewer.cli confirm \
  --session ./sessions/demo.json \
  --industry "数字IC / SoC" \
  --focus "微架构,RTL实现"
```

### 4. 启动模拟面试

最基础的启动方式：

```bash
./.venv/bin/python -m ic_interviewer.cli interview \
  --session ./sessions/demo.json \
  --out ./out/interview_report.md
```

### 5. 指定题目数量

```bash
./.venv/bin/python -m ic_interviewer.cli interview \
  --session ./sessions/demo.json \
  --out ./out/interview_report.md \
  --num-questions 10
```

### 6. 指定题型分布

```bash
./.venv/bin/python -m ic_interviewer.cli interview \
  --session ./sessions/demo.json \
  --out ./out/interview_report.md \
  --num-questions 10 \
  --mix "architecture=3,implementation=4,hybrid=3"
```

说明：

- `--num-questions` 指定总题数
- `--mix` 指定三类题目的数量分布
- `--mix` 三类数量之和必须等于 `--num-questions`
- 当前代码没有 `--lang` CLI 参数
- 语言会在 `interview` 启动后通过交互方式选择
- 如果你直接回车，默认是中文

## 输出文件说明

常见输出文件如下：

- 会话文件：`SESSION_PATH`，例如 `./sessions/demo.json`
- 面试报告：`REPORT_PATH`，例如 `./out/interview_report.md`

其中：

- `session.json` 会保存分析结果、题目、回答、点评等信息
- Markdown 报告会保存最终面试记录与总结

## 补充说明

- `inspect` 只读取 `session.json`，不会修改数据
- `confirm` 用于手动覆盖方向和侧重点
- `interview` 会在正式开始前再次显示配置，让你确认是否开始
- 如果选择英文，题目、点评、标准答案、背诵版和报告会统一切换到英文
