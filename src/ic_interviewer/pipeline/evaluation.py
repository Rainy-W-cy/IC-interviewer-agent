"""Rule-based answer evaluation."""

from __future__ import annotations

from ic_interviewer.models import Evaluation, Question, SessionState


SHORT_ANSWER_THRESHOLD = 8


def _find_project_anchors(session: SessionState, project_name: str, language: str) -> list[str]:
    anchors: list[str] = []
    if not session.resume:
        return anchors

    for project in session.resume.projects:
        if project.name == project_name:
            if language == "en":
                anchors.append(f"Resume: project {project.name}")
                anchors.extend(f"Resume: claim {claim}" for claim in project.claims[:2])
            else:
                anchors.append(f"简历: 项目 {project.name}")
                anchors.extend(f"简历: 主张 {claim}" for claim in project.claims[:2])
            break
    return anchors


def _find_repo_anchors(session: SessionState, question: Question, language: str) -> list[str]:
    anchors: list[str] = []
    files = session.repo_index.get("files") or session.repo_index.get("sample_files") or []
    topic_lower = question.topic.lower()
    project_lower = question.project.lower()
    for file_path in files[:10]:
        lowered = str(file_path).lower()
        if topic_lower in lowered or any(token in lowered for token in project_lower.split()):
            anchors.append(f"{'Repo' if language == 'en' else '仓库'}: {file_path}")
    return anchors[:2]


def _knowledge_anchor(question: Question, language: str) -> str:
    if language != "en":
        if question.type == "architecture":
            return f"知识点: {question.topic} 权衡"
        if question.type == "implementation":
            return f"知识点: {question.topic} 调试路径"
        return f"知识点: {question.topic} 设计到实现的映射"
    if question.type == "architecture":
        return f"Knowledge: {question.topic} trade-off"
    if question.type == "implementation":
        return f"Knowledge: {question.topic} debug path"
    return f"Knowledge: {question.topic} design-to-implementation link"


def _standard_answer(question: Question, language: str) -> str:
    if language != "en":
        if question.type == "architecture":
            return "\n".join(
                [
                    "专业版：",
                    f"1. 设计目标与约束：先说明项目里 {question.topic} 要解决的核心目标，以及性能、复杂度、可验证性等约束。",
                    "2. 备选方案对比：给出至少两种候选方案，并说明各自优缺点。",
                    "3. 最终选择与原因：明确为什么采用当前方案，而不是其他路线。",
                    "4. 模块划分与接口边界：说明模块如何拆分、接口为什么这样定义。",
                    "5. 工程落地影响：解释该方案对实现复杂度、联调效率和后续扩展的影响。",
                    "6. 风险与边界：补充当前方案最容易出问题的地方，以及你如何控制风险。",
                ]
            )
        if question.type == "implementation":
            return "\n".join(
                [
                    "专业版：",
                    f"1. 策略结论：先说明 {question.topic} 相关实现采用了什么核心策略。",
                    "2. 判定路径与优先级：描述关键流程、判断条件或控制顺序。",
                    "3. 一致性保障：说明如何保证状态、数据或接口行为的一致性。",
                    "4. 前进性与无死锁：说明边界场景下如何避免卡死、冲突或错误传播。",
                    "5. 调试与修复闭环：补充一个具体 bug 的定位、修复和验证过程。",
                    "6. 高层取舍：说明为什么实现没有做得更复杂，当前方案的工程取舍是什么。",
                ]
            )
        return "\n".join(
            [
                "专业版：",
                f"1. 设计目标：先说明项目里 {question.topic} 的顶层目标是什么。",
                "2. 落地路径：解释这个目标如何被拆解成模块、接口和具体实现步骤。",
                "3. 实现要点：说明 RTL、控制逻辑或验证点是如何围绕目标展开的。",
                "4. 验证闭环：说明你如何证明实现结果符合原始设计目标。",
                "5. 关键取舍：补充性能、复杂度、验证成本之间最核心的一次取舍。",
            ]
        )
    if question.type == "architecture":
        return "\n".join(
            [
                "Professional version:",
                f"1. Design goal and constraints: explain what {question.topic} needed to achieve and what constraints mattered.",
                "2. Option comparison: compare at least two candidate approaches.",
                "3. Final choice: explain why the final architecture was selected.",
                "4. Module boundaries: describe how modules and interfaces were partitioned.",
                "5. Engineering impact: explain the implementation and verification implications.",
                "6. Risks and boundaries: highlight the main risk and how it was controlled.",
            ]
        )
    if question.type == "implementation":
        return "\n".join(
            [
                "Professional version:",
                f"1. Strategy: summarize the core implementation strategy for {question.topic}.",
                "2. Key flow and priority: explain the major control or data path decisions.",
                "3. Consistency protection: describe how correctness and interface consistency were maintained.",
                "4. Forward progress: explain how deadlock, conflict, or invalid corner behavior was avoided.",
                "5. Debug loop: give one concrete debug, fix, and validation example.",
                "6. Trade-off: explain the engineering trade-off behind the chosen implementation.",
            ]
        )
    return "\n".join(
        [
            "Professional version:",
            f"1. Design goal: explain the top-level goal behind {question.topic}.",
            "2. Landing path: describe how that goal was translated into modules, interfaces, and implementation steps.",
            "3. Implementation details: explain how RTL or verification choices reflected the goal.",
            "4. Validation loop: show how the implementation was checked against the original goal.",
            "5. Trade-off: explain the main trade-off among performance, complexity, and verification cost.",
        ]
    )


def _memorization_answer(question: Question, language: str) -> str:
    if language != "en":
        if question.type == "architecture":
            return (
                f"背诵版：我当时先明确了 {question.topic} 的目标和约束，再比较了几种方案，最后选了综合权衡更合适的路线。"
                "模块划分上，我会优先保证接口清晰、联调方便、后续扩展成本可控。"
            )
        if question.type == "implementation":
            return (
                f"背诵版：我负责把 {question.topic} 相关逻辑按步骤落到实现里，先把主流程跑通，再重点处理边界情况和异常场景。"
                "遇到问题时，我会结合波形、日志和回归结果定位原因，再修复并做防回归确认。"
            )
        return (
            f"背诵版：{question.topic} 的设计目标直接决定了后面的实现方式，所以我会先讲目标，再讲它是怎么落到模块和 RTL 上的。"
            "最后我会补充验证闭环和关键取舍，让面试官看到这不是孤立实现，而是完整工程决策。"
        )
    if question.type == "architecture":
        return (
            f"Memorization version: I started from the {question.topic} goal and constraints, compared a few options, and picked the one with the best overall trade-off. "
            "I also defined module boundaries so integration, debug, and future scaling would stay manageable."
        )
    if question.type == "implementation":
        return (
            f"Memorization version: I implemented the {question.topic} path step by step, stabilized the main flow first, and then focused on edge cases and exceptional scenarios. "
            "When issues appeared, I used waveforms, logs, and regressions to debug, fix, and close them."
        )
    return (
        f"Memorization version: The design goal of {question.topic} directly shaped the implementation choices, so I explain the goal first, then how it landed in modules and RTL. "
        "I close by showing how the result was verified and what trade-off mattered most."
    )


def evaluate_answer(
    question: Question,
    answer: str,
    session: SessionState,
    language: str | None = None,
) -> Evaluation:
    language = language or session.inputs.get("language", "zh")
    normalized = answer.strip()
    word_count = len(normalized.split())

    if language == "en":
        if normalized:
            summary = "Verification result: partially verified. The answer contains useful information and can support deeper follow-up."
            strengths = ["The response provided meaningful content."]
        else:
            summary = "Verification result: needs more detail. The answer is empty, so project depth cannot be assessed."
            strengths = ["At least the candidate responded to the prompt."]
    else:
        if normalized:
            summary = "检验结论：部分成立。回答提供了有效信息，可以继续追问细节。"
            strengths = ["给出了有效回答。"]
        else:
            summary = "检验结论：待补充。回答为空，无法判断项目理解深度。"
            strengths = ["至少完成了当前问题的响应。"]

    gaps: list[str] = []
    if word_count < SHORT_ANSWER_THRESHOLD:
        gaps.append("回答偏简略，缺少项目细节" if language != "en" else "The answer is brief and lacks project-specific detail.")

    anchors = _find_project_anchors(session, question.project, language)
    anchors.extend(_find_repo_anchors(session, question, language))
    anchors.append(_knowledge_anchor(question, language))

    seen: set[str] = set()
    deduped_anchors: list[str] = []
    for anchor in anchors:
        if anchor not in seen:
            deduped_anchors.append(anchor)
            seen.add(anchor)

    return Evaluation(
        summary=summary,
        strengths=strengths,
        gaps=gaps,
        anchors=deduped_anchors,
        standard_answer=_standard_answer(question, language),
        memorization_answer=_memorization_answer(question, language),
    )
