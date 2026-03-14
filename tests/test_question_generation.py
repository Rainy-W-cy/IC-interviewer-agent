from collections import Counter

from ic_interviewer.models import Profile, ResumeData, ResumeProject, SessionState
from ic_interviewer.pipeline.interview import generate_questions, resolve_question_mix


def make_session() -> SessionState:
    return SessionState(
        session_id="session-questions",
        inputs={"resume_path": "resume.md"},
        resume=ResumeData(
            candidate_name="Alice Zhang",
            skills=["RTL", "AXI", "UVM", "FPGA"],
            projects=[
                ResumeProject(
                    name="RISC-V CPU",
                    summary="Implemented a 5-stage CPU.",
                    claims=[
                        "Designed a forwarding path for pipeline hazards.",
                        "Integrated AXI access for memory transactions.",
                    ],
                    keywords=["RTL", "AXI", "pipeline"],
                ),
                ResumeProject(
                    name="FPGA Accelerator",
                    summary="Built a Zynq-based accelerator.",
                    claims=[
                        "Implemented DMA data movement.",
                        "Debugged timing and interface bring-up issues.",
                    ],
                    keywords=["FPGA", "Vivado", "stall"],
                ),
                ResumeProject(
                    name="Extra Project",
                    summary="Should not be used for first-pass questions.",
                    claims=["Unused claim"],
                    keywords=["unused"],
                ),
            ],
        ),
        profile=Profile(
            industry="Digital IC / SoC",
            focus=["Verification"],
            secondary_focus=["Digital Design"],
            question_mix={"project": 0.5, "verification": 0.5},
            reasons=["Matched IC keywords."],
        ),
    )


def test_generate_questions_returns_requested_question_count() -> None:
    session = make_session()

    questions = generate_questions(session, num_questions=6)

    assert len(questions) == 6
    counts = Counter(question.type for question in questions)
    assert counts == {"architecture": 2, "implementation": 2, "hybrid": 2}


def test_generate_questions_prioritizes_first_two_projects() -> None:
    session = make_session()

    questions = generate_questions(session, num_questions=6)

    assert {question.project for question in questions} == {"RISC-V CPU", "FPGA Accelerator"}
    assert [question.id for question in questions] == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
    assert all(question.topic for question in questions)
    assert any(question.topic == "RTL实现" for question in questions)
    assert any(question.topic == "FPGA实现" for question in questions)
    assert all(question.question for question in questions)


def test_generate_questions_uses_reasonable_templates() -> None:
    session = make_session()

    questions = generate_questions(session, num_questions=6)

    architecture = [question for question in questions if question.type == "architecture"]
    implementation = [question for question in questions if question.type == "implementation"]
    hybrid = [question for question in questions if question.type == "hybrid"]

    assert all(
        ("目标" in question.question or "要解决什么问题" in question.question)
        and "模块" in question.question
        and ("取舍" in question.question or "权衡" in question.question)
        for question in architecture
    )
    assert all(
        ("具体负责" in question.question or "关键流程" in question.question or "责任范围" in question.question)
        and (
            "边界情况" in question.question
            or "异常场景" in question.question
            or "边界输入" in question.question
            or "边界问题" in question.question
        )
        and ("调试" in question.question or "调试经历" in question.question or "修复" in question.question)
        for question in implementation
    )
    assert all(
        "设计目标" in question.question
        and ("具体实现" in question.question or "实现步骤" in question.question)
        and ("取舍" in question.question or "权衡" in question.question)
        for question in hybrid
    )


def test_generate_questions_supports_more_than_six_without_simple_repetition() -> None:
    session = make_session()

    questions = generate_questions(session, num_questions=8)

    assert len(questions) == 8
    counts = Counter(question.type for question in questions)
    assert counts == {"architecture": 3, "implementation": 3, "hybrid": 2}
    assert set(counts) == {"architecture", "implementation", "hybrid"}
    assert len({question.question for question in questions}) >= 6
    assert all(question.question.strip() for question in questions)
    assert all(any("\u4e00" <= char <= "\u9fff" for char in question.question) for question in questions)


def test_resolve_question_mix_balances_evenly_when_mix_not_provided() -> None:
    mix = resolve_question_mix(8, None)

    assert mix == {"architecture": 3, "implementation": 3, "hybrid": 2}


def test_resolve_question_mix_parses_explicit_distribution() -> None:
    mix = resolve_question_mix(8, "architecture=2,implementation=3,hybrid=3")

    assert mix == {"architecture": 2, "implementation": 3, "hybrid": 3}


def test_resolve_question_mix_raises_clear_error_for_invalid_total() -> None:
    try:
        resolve_question_mix(8, "architecture=3,implementation=3,hybrid=3")
    except ValueError as exc:
        assert str(exc) == "题型分布总数为 9，与题目总数 8 不一致"
    else:
        raise AssertionError("Expected ValueError for invalid mix total")
