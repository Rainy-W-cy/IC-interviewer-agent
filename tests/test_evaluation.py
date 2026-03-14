from ic_interviewer.models import Profile, Question, ResumeData, ResumeProject, SessionState
from ic_interviewer.pipeline.evaluation import evaluate_answer


def make_session() -> SessionState:
    return SessionState(
        session_id="session-eval",
        inputs={"resume_path": "resume.md"},
        resume=ResumeData(
            candidate_name="Alice",
            skills=["RTL", "AXI", "UVM"],
            projects=[
                ResumeProject(
                    name="RISC-V CPU",
                    summary="Implemented a 5-stage CPU.",
                    claims=[
                        "Designed forwarding logic for pipeline hazards.",
                        "Integrated AXI transactions on the memory side.",
                    ],
                    keywords=["pipeline", "AXI"],
                )
            ],
        ),
        profile=Profile(
            industry="Digital IC / SoC",
            focus=["Verification"],
            secondary_focus=["Digital Design"],
            question_mix={"project": 0.5, "verification": 0.5},
            reasons=["Matched keywords."],
        ),
        repo_index={
            "files": ["rtl/cpu_top.sv", "uvm/scoreboard.sv"],
            "symbols": ["rtl/cpu_top.sv:cpu_top"],
            "topics": ["pipeline", "axi", "scoreboard"],
            "indexed": True,
            "file_count": 2,
            "sample_files": ["rtl/cpu_top.sv", "uvm/scoreboard.sv"],
        },
    )


def test_evaluate_answer_generates_required_fields() -> None:
    session = make_session()
    question = Question(
        id="q01",
        type="architecture",
        project="RISC-V CPU",
        topic="pipeline",
        question="How did you choose the architecture?",
    )

    evaluation = evaluate_answer(question, "I compared a few pipeline depth options and chose five stages.", session)

    assert evaluation.summary
    assert evaluation.strengths
    assert evaluation.gaps == []
    assert "简历: 项目 RISC-V CPU" in evaluation.anchors
    assert "仓库: rtl/cpu_top.sv" in evaluation.anchors
    assert "知识点: pipeline 权衡" in evaluation.anchors
    assert evaluation.standard_answer
    assert evaluation.memorization_answer


def test_evaluate_answer_marks_short_answer_gap() -> None:
    session = make_session()
    question = Question(
        id="q02",
        type="implementation",
        project="RISC-V CPU",
        topic="AXI",
        question="How did you implement AXI?",
    )

    evaluation = evaluate_answer(question, "I implemented AXI.", session)

    assert evaluation.strengths
    assert "回答偏简略，缺少项目细节" in evaluation.gaps
    assert "知识点: AXI 调试路径" in evaluation.anchors


def test_evaluate_answer_handles_empty_answer_with_fallback_anchors() -> None:
    session = make_session()
    question = Question(
        id="q03",
        type="hybrid",
        project="Unknown Project",
        topic="scoreboard",
        question="How did architecture map to implementation?",
    )

    evaluation = evaluate_answer(question, "", session)

    assert evaluation.summary == "检验结论：待补充。回答为空，无法判断项目理解深度。"
    assert evaluation.strengths
    assert "回答偏简略，缺少项目细节" in evaluation.gaps
    assert "仓库: uvm/scoreboard.sv" in evaluation.anchors
    assert "知识点: scoreboard 设计到实现的映射" in evaluation.anchors


def test_evaluate_answer_supports_english_output() -> None:
    session = make_session()
    session.inputs["language"] = "en"
    question = Question(
        id="Q4",
        type="architecture",
        project="RISC-V CPU",
        topic="pipeline design",
        question="How did you choose the architecture?",
    )

    evaluation = evaluate_answer(question, "I compared two options and picked the lower-latency one.", session)

    assert evaluation.summary.startswith("Verification result: partially verified.")
    assert evaluation.strengths == ["The response provided meaningful content."]
    assert "Resume: project RISC-V CPU" in evaluation.anchors
    assert "Knowledge: pipeline design trade-off" in evaluation.anchors
    assert evaluation.standard_answer.startswith("Professional version:")
