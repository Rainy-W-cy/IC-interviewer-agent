"""Rule-based interview question generation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Callable

from ic_interviewer.models import QALog, Question, ResumeProject, SessionState
from ic_interviewer.pipeline.evaluation import evaluate_answer
from ic_interviewer.report import write_markdown_report

QUESTION_TYPE_LABELS = {
    "architecture": "架构类",
    "implementation": "实现类",
    "hybrid": "混合类",
}
QUESTION_TYPES = ("architecture", "implementation", "hybrid")
DEFAULT_NUM_QUESTIONS = 6
DEFAULT_LANGUAGE = "zh"
TOPIC_LABELS = {
    "rtl": "RTL实现",
    "axi": "AXI总线",
    "pipeline": "流水线设计",
    "hazard": "冒险处理",
    "forwarding": "前递机制",
    "stall": "停顿控制",
    "uvm": "UVM验证环境",
    "scoreboard": "Scoreboard机制",
    "verification": "验证策略",
    "digital design": "数字设计",
    "fpga": "FPGA实现",
    "vivado": "Vivado流程",
    "design tradeoff": "设计权衡",
}
TOPIC_LABELS_EN = {
    "rtl": "RTL implementation",
    "axi": "AXI bus",
    "pipeline": "pipeline design",
    "hazard": "hazard handling",
    "forwarding": "forwarding logic",
    "stall": "stall control",
    "uvm": "UVM environment",
    "scoreboard": "scoreboard mechanism",
    "verification": "verification strategy",
    "digital design": "digital design",
    "fpga": "FPGA implementation",
    "vivado": "Vivado flow",
    "design tradeoff": "design trade-off",
}


def _pick_projects(session: SessionState) -> list[ResumeProject]:
    if session.resume and session.resume.projects:
        return session.resume.projects[:2]

    return [
        ResumeProject(
            name="General Experience",
            summary="Candidate resume did not expose project details.",
            claims=["Walk through the most representative IC project you built."],
            keywords=[],
        )
    ]


def _pick_topic(project: ResumeProject, fallback: str, language: str) -> str:
    raw_topic = fallback
    if project.keywords:
        raw_topic = project.keywords[0]
    elif project.claims:
        words = project.claims[0].split()
        if words:
            raw_topic = words[0]
    if language == "en":
        return TOPIC_LABELS_EN.get(raw_topic.lower(), raw_topic)
    return TOPIC_LABELS.get(raw_topic.lower(), raw_topic)


ARCHITECTURE_TEMPLATES = (
    "在项目《{project}》中，你当时的整体设计目标是什么？围绕 {topic} 你比较过哪些方案，最终为什么选择当前方案？各个模块是如何划分的，关键权衡点又是什么？",
    "针对项目《{project}》，请从整体架构角度说明 {topic} 相关模块要解决什么问题。你当时评估过哪些不同方案，接口边界怎么定义，最终取舍依据是什么？",
    "如果回到项目《{project}》的架构设计阶段，围绕 {topic} 你会先确定哪些顶层目标？模块之间如何拆分职责，哪些指标决定了最终方案？",
    "在项目《{project}》里，{topic} 对整体系统的作用是什么？请说明你如何做模块划分，以及在性能、复杂度和可维护性之间如何权衡。",
    "请结合项目《{project}》说明：为了满足 {topic} 的需求，你们的顶层架构是如何组织的？不同模块边界为什么这样定义？",
    "在项目《{project}》中，围绕 {topic} 做架构设计时，你主要面对哪些方案选择？为什么没有采用其他看似更直接的实现路线？",
    "如果让你向新同事解释项目《{project}》的架构，你会怎样描述 {topic} 相关模块的分工、接口和关键取舍？",
    "对于项目《{project}》，请说明 {topic} 的系统目标、模块划分方式，以及你如何评估当前架构在扩展性和验证成本上的优劣。",
)
ARCHITECTURE_TEMPLATES_EN = (
    "In project '{project}', what was the overall design goal, which options did you compare around {topic}, why did you choose the final approach, and how did you split module boundaries?",
    "For project '{project}', explain what problem the {topic} architecture needed to solve, how you defined interfaces across modules, and what trade-offs drove the final decision.",
    "If you go back to the architecture phase of project '{project}', what top-level goals would you set around {topic}, how would you divide module responsibilities, and which metrics would decide the final plan?",
    "In project '{project}', what role did {topic} play in the full system, how did you partition the modules, and how did you balance performance, complexity, and maintainability?",
    "Using project '{project}' as an example, describe how the top-level architecture was organized to support {topic}, why module boundaries were defined that way, and what trade-offs mattered most.",
    "In project '{project}', what architecture choices did you face around {topic}, and why did you avoid other seemingly simpler implementations?",
    "If you had to explain the architecture of project '{project}' to a new teammate, how would you describe the responsibilities, interfaces, and trade-offs of the {topic} related modules?",
    "For project '{project}', explain the system goal of {topic}, the module partitioning strategy, and how you evaluated scalability versus verification cost.",
)

IMPLEMENTATION_TEMPLATES = (
    "在项目《{project}》中，你具体负责了哪些与 {topic} 相关的内容？请说明实现路径、遇到过哪些边界情况，以及你是如何定位和调试问题的。",
    "在项目《{project}》里，与你负责的 {topic} 实现相关的关键流程是什么？请说明代码或模块落地方式、异常场景处理，以及一次具体调试经历。",
    "请结合项目《{project}》说明：{topic} 这一部分的关键流程是什么，你从哪里开始实现？遇到过哪些边界情况或异常输入，中间踩过哪些坑，最后又是如何调试并把问题收敛掉的？",
    "在项目《{project}》中，围绕 {topic} 的实现你承担了哪些具体工作？如果出现边界输入或时序异常，你通常如何分析和修复？",
    "对于项目《{project}》，请具体讲讲 {topic} 的实现步骤、核心数据通路或控制逻辑，以及一次让你印象深刻的调试过程。",
    "在项目《{project}》里，{topic} 相关模块从设计到代码落地的过程是怎样的？其中哪些边界情况最容易出错，你如何验证修复是否有效？",
    "请以项目《{project}》为例，说明你如何实现 {topic}，如何处理异常场景，以及如何借助波形、日志或回归结果完成调试。",
    "在项目《{project}》中，如果让你复盘 {topic} 的实现工作，你会如何拆解责任范围、实现路径、边界问题和调试闭环？",
)
IMPLEMENTATION_TEMPLATES_EN = (
    "In project '{project}', what parts related to {topic} were you directly responsible for, what implementation path did you take, what edge cases appeared, and how did you debug them?",
    "In project '{project}', what was the key implementation flow for {topic}, how did the code or modules land in practice, how were exceptional cases handled, and what debugging experience stands out?",
    "Using project '{project}' as an example, what was the key flow of the {topic} implementation, where did you start, what edge conditions or invalid inputs showed up, and how did you debug them to closure?",
    "In project '{project}', what concrete work did you own for {topic}, and if boundary inputs or timing problems appeared, how would you analyze and fix them?",
    "For project '{project}', walk through the implementation steps of {topic}, the core datapath or control logic, and one memorable debugging case.",
    "In project '{project}', what was the process from design to code for the {topic} related module, which edge cases were most error-prone, and how did you validate the fix?",
    "Using project '{project}', explain how you implemented {topic}, how you handled exceptional scenarios, and how you used waveforms, logs, or regressions to complete debugging.",
    "If you were to review the implementation of {topic} in project '{project}', how would you break down the ownership scope, implementation path, edge issues, and debugging loop?",
)

HYBRID_TEMPLATES = (
    "在项目《{project}》中，围绕 {topic} 的设计目标是如何一步步落实到具体实现上的？如果当时存在性能、面积、复杂度或验证成本之间的取舍，你是如何做决策的？",
    "在项目《{project}》中，最初的 {topic} 设计目标是如何映射成具体模块、接口和实现步骤的？如果重新做一次，这里面你会如何重新权衡性能、复杂度和可验证性？",
    "请结合项目《{project}》说明：{topic} 的设计目标是什么，这个目标最终怎样落到了具体实现、RTL、验证点或接口设计上？过程中有哪些取舍？",
    "在项目《{project}》里，围绕 {topic} 的高层目标和底层实现之间是如何对齐的？如果目标和实现成本冲突，你会怎么做权衡？",
    "如果以项目《{project}》为例，请你讲清楚 {topic} 从设计目标到模块实现的传导路径，以及中间最关键的一次取舍决策。",
    "在项目《{project}》中，针对 {topic} 的系统目标，你们是如何将其拆解为可实现的模块和控制逻辑的？这个过程中你如何处理取舍问题？",
    "请说明项目《{project}》中 {topic} 的目标、落地实现和验证方式之间的关系。如果三者不能同时最优，你如何做取舍？",
    "回顾项目《{project}》时，针对 {topic} 你会如何把架构目标、实现方案和验证成本串起来说明？哪些地方最体现设计取舍？",
)
HYBRID_TEMPLATES_EN = (
    "In project '{project}', how was the design goal around {topic} translated step by step into the final implementation, and how did you make trade-offs among performance, area, complexity, and verification cost?",
    "In project '{project}', how was the original {topic} design goal mapped into concrete modules, interfaces, and implementation steps, and what would you rebalance if you redesigned it today?",
    "Using project '{project}', explain the design goal of {topic}, how it finally landed in implementation, RTL, verification points, or interface design, and what trade-offs were involved.",
    "In project '{project}', how were the high-level goals of {topic} aligned with the low-level implementation, and what would you do when the goal conflicted with implementation cost?",
    "Using project '{project}' as an example, explain the path from the design goal of {topic} to the module implementation, and describe the most important trade-off decision in the middle.",
    "In project '{project}', how did you decompose the system goal of {topic} into implementable modules and control logic, and how did you handle the trade-offs during that process?",
    "Explain the relationship among the goal, implementation, and verification strategy of {topic} in project '{project}'. If all three could not be optimal at once, how would you make the trade-off?",
    "Looking back at project '{project}', how would you connect the architecture goal, implementation strategy, and verification cost of {topic}, and which points best show the design trade-offs?",
)


def generate_questions(
    session: SessionState,
    num_questions: int = DEFAULT_NUM_QUESTIONS,
    mix: dict[str, int] | None = None,
    language: str = DEFAULT_LANGUAGE,
) -> list[Question]:
    if num_questions <= 0:
        raise ValueError("num_questions must be a positive integer.")

    projects = _pick_projects(session)
    if len(projects) == 1:
        projects = [projects[0], projects[0]]

    focus_terms: list[str] = []
    if session.profile:
        focus_terms.extend(session.profile.focus)
        focus_terms.extend(session.profile.secondary_focus)

    if language == "en":
        template_pool: dict[str, Sequence[str]] = {
            "architecture": ARCHITECTURE_TEMPLATES_EN,
            "implementation": IMPLEMENTATION_TEMPLATES_EN,
            "hybrid": HYBRID_TEMPLATES_EN,
        }
    else:
        template_pool = {
            "architecture": ARCHITECTURE_TEMPLATES,
            "implementation": IMPLEMENTATION_TEMPLATES,
            "hybrid": HYBRID_TEMPLATES,
        }
    type_order = list(QUESTION_TYPES)
    if mix:
        expanded_types: list[str] = []
        for question_type in type_order:
            expanded_types.extend([question_type] * max(mix.get(question_type, 0), 0))
        type_sequence = expanded_types or type_order
    else:
        type_sequence = type_order

    questions: list[Question] = []
    for index in range(1, num_questions + 1):
        question_type = type_sequence[(index - 1) % len(type_sequence)]
        project = projects[(index - 1) % min(len(projects), 2)]
        templates = template_pool[question_type]
        template = templates[((index - 1) // len(projects)) % len(templates)]
        fallback_topic = focus_terms[(index - 1) % len(focus_terms)] if focus_terms else ("design tradeoff" if language == "en" else "设计权衡")
        topic = _pick_topic(project, fallback_topic, language)
        questions.append(
            Question(
                id=f"Q{index}",
                type=question_type,
                project=project.name,
                topic=topic,
                question=template.format(project=project.name, topic=topic),
            )
        )

    return questions


def resolve_question_mix(num_questions: int, mix_text: str | None = None) -> dict[str, int]:
    if num_questions <= 0:
        raise ValueError("题目总数必须是正整数。")

    if mix_text is None:
        base = num_questions // len(QUESTION_TYPES)
        remainder = num_questions % len(QUESTION_TYPES)
        distribution = {question_type: base for question_type in QUESTION_TYPES}
        for question_type in QUESTION_TYPES[:remainder]:
            distribution[question_type] += 1
        return distribution

    distribution = {question_type: 0 for question_type in QUESTION_TYPES}
    seen: set[str] = set()
    entries = [item.strip() for item in mix_text.split(",") if item.strip()]
    if not entries:
        raise ValueError("题型分布格式无效，应为 architecture=3,implementation=4,hybrid=3")

    for entry in entries:
        if "=" not in entry:
            raise ValueError("题型分布格式无效，应为 architecture=3,implementation=4,hybrid=3")
        key, value = [part.strip() for part in entry.split("=", 1)]
        if key not in distribution:
            raise ValueError(
                "题型分布包含不支持的类型，仅支持 architecture、implementation、hybrid"
            )
        if key in seen:
            raise ValueError(f"题型分布中重复指定了 {key}")
        if not value.isdigit():
            raise ValueError(f"题型分布中 {key} 的数量不是非负整数")
        distribution[key] = int(value)
        seen.add(key)

    total = sum(distribution.values())
    if total != num_questions:
        raise ValueError(f"题型分布总数为 {total}，与题目总数 {num_questions} 不一致")

    return distribution


def resolve_language(
    language: str | None = None,
    existing_language: str | None = None,
    input_func: Callable[[str], str] | None = None,
    output_func: Callable[[str], None] | None = None,
) -> str:
    if language in {"zh", "en"}:
        return language
    if existing_language in {"zh", "en"}:
        return existing_language
    input_func = input_func or input
    output_func = output_func or print
    output_func("请选择本次面试与报告语言（中文/英文，默认中文）：")
    while True:
        raw_value = input_func("> ").strip().lower()
        if raw_value in {"", "中文", "zh", "cn"}:
            return "zh"
        if raw_value in {"英文", "english", "en"}:
            return "en"
        output_func("输入无效，请输入 中文 或 英文。")


def resolve_num_questions(
    num_questions: int | None = None,
    input_func: Callable[[str], str] | None = None,
    output_func: Callable[[str], None] | None = None,
) -> int:
    if num_questions is not None:
        if num_questions <= 0:
            raise ValueError("题目数量必须是正整数。")
        return num_questions

    input_func = input_func or input
    output_func = output_func or print
    prompt = f"请输入本次模拟面试的题目数量（默认 {DEFAULT_NUM_QUESTIONS}）："

    while True:
        output_func(prompt)
        raw_value = input_func("> ").strip()
        if not raw_value:
            return DEFAULT_NUM_QUESTIONS
        if raw_value.isdigit() and int(raw_value) > 0:
            return int(raw_value)
        output_func("输入无效，请输入正整数。")


def _ask_customize_mix(
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> bool:
    output_func("是否自定义题型分布？(y/N)：")
    while True:
        raw_value = input_func("> ").strip().lower()
        if raw_value in {"", "n", "no", "否"}:
            return False
        if raw_value in {"y", "yes", "是"}:
            return True
        output_func("输入无效，请输入 y 或 n。")


def _ask_mix_counts(
    num_questions: int,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> dict[str, int]:
    while True:
        output_func("请输入架构类题目数量：")
        architecture = _prompt_non_negative_int(input_func, output_func)
        output_func("请输入实现类题目数量：")
        implementation = _prompt_non_negative_int(input_func, output_func)
        output_func("请输入混合类题目数量：")
        hybrid = _prompt_non_negative_int(input_func, output_func)
        total = architecture + implementation + hybrid
        if total == num_questions:
            return {
                "architecture": architecture,
                "implementation": implementation,
                "hybrid": hybrid,
            }
        output_func(f"三类题目数量之和为 {total}，与总题数 {num_questions} 不一致，请重新输入。")


def _prompt_positive_int(
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> int:
    while True:
        raw_value = input_func("> ").strip()
        if raw_value.isdigit() and int(raw_value) > 0:
            return int(raw_value)
        output_func("输入无效，请输入正整数。")


def _prompt_non_negative_int(
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> int:
    while True:
        raw_value = input_func("> ").strip()
        if raw_value.isdigit():
            return int(raw_value)
        output_func("输入无效，请输入非负整数。")


def resolve_interview_plan(
    num_questions: int | None = None,
    mix_text: str | None = None,
    input_func: Callable[[str], str] | None = None,
    output_func: Callable[[str], None] | None = None,
) -> tuple[int, dict[str, int]]:
    input_func = input_func or input
    output_func = output_func or print

    if mix_text is not None:
        parsed_total = None
        entries = [item.strip() for item in mix_text.split(",") if item.strip()]
        temp_total = 0
        for entry in entries:
            if "=" not in entry:
                raise ValueError("题型分布格式无效，应为 architecture=3,implementation=4,hybrid=3")
            _, value = [part.strip() for part in entry.split("=", 1)]
            if not value.isdigit():
                raise ValueError("题型分布格式无效，应为 architecture=3,implementation=4,hybrid=3")
            temp_total += int(value)
        parsed_total = temp_total
        resolved_num_questions = resolve_num_questions(
            num_questions=num_questions if num_questions is not None else parsed_total,
            input_func=input_func,
            output_func=output_func,
        )
        return resolved_num_questions, resolve_question_mix(resolved_num_questions, mix_text)

    resolved_num_questions = resolve_num_questions(
        num_questions=num_questions,
        input_func=input_func,
        output_func=output_func,
    )
    if num_questions is None:
        customize = _ask_customize_mix(input_func, output_func)
        if customize:
            return resolved_num_questions, _ask_mix_counts(resolved_num_questions, input_func, output_func)
    return resolved_num_questions, resolve_question_mix(resolved_num_questions, None)


def confirm_interview_plan(
    num_questions: int,
    mix: dict[str, int],
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> bool:
    output_func("本次模拟面试配置如下：")
    output_func(f"- 总题数：{num_questions}")
    output_func(f"- 架构类：{mix['architecture']}")
    output_func(f"- 实现类：{mix['implementation']}")
    output_func(f"- 混合类：{mix['hybrid']}")
    output_func("是否开始？(Y/n)：")
    while True:
        raw_value = input_func("> ").strip().lower()
        if raw_value in {"", "y", "yes", "是"}:
            return True
        if raw_value in {"n", "no", "否"}:
            return False
        output_func("输入无效，请输入 y 或 n。")


def run_interview(
    session_path: str,
    out_path: str,
    num_questions: int | None = None,
    mix_text: str | None = None,
    language: str | None = None,
    input_func: Callable[[str], str] | None = None,
    output_func: Callable[[str], None] | None = None,
) -> SessionState:
    session_file = Path(session_path)
    state = SessionState.from_file(session_file)
    input_func = input_func or input
    output_func = output_func or print
    resolved_language = resolve_language(
        language=language,
        existing_language=state.inputs.get("language") if state.inputs else None,
        input_func=input_func,
        output_func=output_func,
    )
    state.inputs["language"] = resolved_language
    resolved_num_questions, resolved_mix = resolve_interview_plan(
        num_questions=num_questions,
        mix_text=mix_text,
        input_func=input_func,
        output_func=output_func,
    )
    if not confirm_interview_plan(
        num_questions=resolved_num_questions,
        mix=resolved_mix,
        input_func=input_func,
        output_func=output_func,
    ):
        output_func("已取消本次模拟面试。")
        return state

    if not state.questions or len(state.questions) != resolved_num_questions:
        state.questions = generate_questions(
            state,
            num_questions=resolved_num_questions,
            mix=resolved_mix,
            language=resolved_language,
        )
        state.qa_log = []
        state.save_to_file(session_file)

    qa_log: list[QALog] = []

    for index, question in enumerate(state.questions, start=1):
        type_label = QUESTION_TYPE_LABELS.get(question.type, question.type)
        if resolved_language == "en":
            type_label = {
                "architecture": "Architecture",
                "implementation": "Implementation",
                "hybrid": "Hybrid",
            }.get(question.type, question.type)
        output_func(f"[Q{index}][{type_label}][{question.project}]")
        output_func(question.question)
        output_func("Your answer:" if resolved_language == "en" else "你的回答：")
        answer = input_func("> ")
        evaluation = evaluate_answer(question, answer, state, language=resolved_language)

        qa_entry = QALog(question=question, answer=answer, evaluation=evaluation)
        qa_log.append(qa_entry)

        state.qa_log = qa_log
        state.save_to_file(session_file)

    state.report_path = str(Path(out_path))
    state.save_to_file(session_file)
    write_markdown_report(state, out_path)
    return state
