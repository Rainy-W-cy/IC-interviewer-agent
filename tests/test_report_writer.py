from pathlib import Path

from ic_interviewer.models import Evaluation, Profile, QALog, Question, ResumeData, ResumeProject, SessionState
from ic_interviewer.report.writer import write_markdown_report


def make_session() -> SessionState:
    question = Question(
        id="q01",
        type="architecture",
        project="RISC-V CPU",
        topic="pipeline",
        question="How did you choose the architecture?",
    )
    evaluation = Evaluation(
        summary="回答较清晰，能覆盖主要权衡。",
        strengths=["给出了有效回答。"],
        gaps=["回答偏简略，缺少项目细节"],
        anchors=["Resume: project RISC-V CPU", "Repo: rtl/cpu_top.sv", "Knowledge: pipeline trade-off"],
        standard_answer="A strong answer should compare options and explain boundaries.",
        memorization_answer="I compared a few options and chose the best trade-off.",
    )
    return SessionState(
        session_id="session-report",
        inputs={"resume_path": "examples/resume.md", "repo_path": "examples/candidate_repo"},
        resume=ResumeData(
            candidate_name="Alice",
            skills=["RTL", "AXI"],
            projects=[
                ResumeProject(
                    name="RISC-V CPU",
                    summary="Implemented a 5-stage CPU.",
                    claims=["Designed forwarding logic.", "Integrated AXI transactions."],
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
        qa_log=[QALog(question=question, answer="I compared several pipeline depths.", evaluation=evaluation)],
    )


def test_write_markdown_report_renders_expected_sections(tmp_path: Path) -> None:
    session = make_session()
    out_path = tmp_path / "interview_report.md"

    write_markdown_report(session, str(out_path))

    content = out_path.read_text(encoding="utf-8")
    assert "# 集成电路模拟面试报告" in content
    assert "## 一、候选人画像" in content
    assert "- 简历路径: examples/resume.md" in content
    assert "## 二、项目摘要" in content
    assert "- RISC-V CPU" in content
    assert "## 三、面试问答记录" in content
    assert "### Q1 [Architecture] - RISC-V CPU" in content
    assert "**候选人回答**" in content
    assert "Resume: project RISC-V CPU" in content
    assert "**参考标准答案**" in content
    assert "**面试背诵版**" in content
    assert "## 四、总体建议" in content


def test_write_markdown_report_creates_parent_directory(tmp_path: Path) -> None:
    session = make_session()
    out_path = tmp_path / "out" / "nested" / "interview_report.md"

    write_markdown_report(session, str(out_path))

    assert out_path.exists()


def test_write_markdown_report_supports_english_language(tmp_path: Path) -> None:
    session = make_session()
    session.inputs["language"] = "en"
    session.qa_log[0].evaluation.standard_answer = "A strong answer should compare options."
    session.qa_log[0].evaluation.memorization_answer = "I compared the options and chose the best one."
    out_path = tmp_path / "interview_report_en.md"

    write_markdown_report(session, str(out_path))

    content = out_path.read_text(encoding="utf-8")
    assert "# IC Mock Interview Report" in content
    assert "## 1. Candidate Profile" in content
    assert "**Standard Answer**" in content
    assert "**Memorization Version**" in content
