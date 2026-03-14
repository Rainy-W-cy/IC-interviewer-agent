from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ic_interviewer.cli import app
from ic_interviewer.models import Profile, ResumeData, ResumeProject, SessionState


def make_session(tmp_path: Path) -> Path:
    session_path = tmp_path / "session.json"
    state = SessionState(
        session_id="session-interview",
        inputs={"resume_path": "resume.md"},
        resume=ResumeData(
            candidate_name="Alice",
            skills=["RTL", "UVM"],
            projects=[
                ResumeProject(
                    name="RISC-V CPU",
                    summary="Implemented a CPU.",
                    claims=["Built forwarding logic."],
                    keywords=["pipeline", "axi"],
                ),
                ResumeProject(
                    name="UVM TB",
                    summary="Implemented a verification environment.",
                    claims=["Built scoreboard and sequences."],
                    keywords=["uvm", "scoreboard"],
                ),
            ],
        ),
        profile=Profile(
            industry="Digital IC / SoC",
            focus=["Verification"],
            secondary_focus=["Digital Design"],
            question_mix={"project": 0.5, "verification": 0.5},
            reasons=["Matched keywords."],
        ),
    )
    state.save_to_file(session_path)
    return session_path


def test_interview_cli_collects_answers_and_writes_session(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    answers = [f"answer {index}" for index in range(1, 7)]

    with patch("builtins.input", side_effect=["中文", "", *answers]):
        result = runner.invoke(
            app,
            [
                "interview",
                "--session",
                str(session_path),
                "--out",
                str(out_path),
                "--num-questions",
                "6",
            ],
        )

    assert result.exit_code == 0
    assert "请选择本次面试与报告语言（中文/英文，默认中文）：" in result.stdout
    assert "本次模拟面试配置如下：" in result.stdout
    assert "- 总题数：6" in result.stdout
    assert "[Q1][架构类][RISC-V CPU]" in result.stdout
    assert "你的回答：" in result.stdout
    assert "Interview complete: 6 answers saved" in result.stdout

    session = SessionState.from_file(session_path)
    assert len(session.questions) == 6
    assert len(session.qa_log) == 6
    assert session.qa_log[0].answer == "answer 1"
    assert session.qa_log[0].evaluation is not None
    assert session.report_path == str(out_path)
    assert out_path.exists()
    assert "# 集成电路模拟面试报告" in out_path.read_text(encoding="utf-8")


def test_interview_cli_supports_num_questions_8(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    answers = "\n\n" + "\n".join(f"answer {index}" for index in range(1, 9)) + "\n"

    result = runner.invoke(
        app,
        [
            "interview",
            "--session",
            str(session_path),
            "--out",
            str(out_path),
            "--num-questions",
            "8",
        ],
        input=answers,
    )

    assert result.exit_code == 0
    assert "- 总题数：8" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert len(loaded.questions) == 8
    assert len(loaded.qa_log) == 8
    types = [question.type for question in loaded.questions]
    assert "architecture" in types
    assert "implementation" in types
    assert "hybrid" in types


def test_interview_reuses_existing_questions(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    state = SessionState.from_file(session_path)
    state.questions = state.questions or []
    state.questions = state.questions[:0]
    state.save_to_file(session_path)

    with patch("builtins.input", side_effect=["中文", "", "a1", "a2", "a3", "a4", "a5", "a6"]):
        runner.invoke(
            app,
            ["interview", "--session", str(session_path), "--out", str(out_path), "--num-questions", "6"],
        )

    loaded = SessionState.from_file(session_path)
    assert len(loaded.questions) == 6


def test_interview_cli_prompts_for_question_count_and_accepts_default(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    inputs = "\n\n\n\n" + "\n".join(f"answer {index}" for index in range(1, 7)) + "\n"

    result = runner.invoke(
        app,
        ["interview", "--session", str(session_path), "--out", str(out_path)],
        input=inputs,
    )

    assert result.exit_code == 0
    assert "请输入本次模拟面试的题目数量（默认 6）：" in result.stdout
    assert "是否自定义题型分布？(y/N)：”" not in result.stdout
    assert "是否自定义题型分布？(y/N)：" in result.stdout
    assert "是否开始？(Y/n)：" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert len(loaded.questions) == 6


def test_interview_cli_reprompts_for_invalid_question_count(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    inputs = "\nabc\n0\n4\n\n\nans1\nans2\nans3\nans4\n"

    result = runner.invoke(
        app,
        ["interview", "--session", str(session_path), "--out", str(out_path)],
        input=inputs,
    )

    assert result.exit_code == 0
    assert "输入无效，请输入正整数。" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert len(loaded.questions) == 4
    assert len(loaded.qa_log) == 4


def test_interview_cli_accepts_explicit_mix_without_num_questions(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    answers = "\n\n" + "a1\na2\na3\na4\na5\na6\na7\na8\na9\na10\n"

    result = runner.invoke(
        app,
        [
            "interview",
            "--session",
            str(session_path),
            "--out",
            str(out_path),
            "--mix",
            "architecture=3,implementation=4,hybrid=3",
        ],
        input=answers,
    )

    assert result.exit_code == 0
    assert "- 总题数：10" in result.stdout
    assert "- 架构类：3" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert len(loaded.questions) == 10
    types = [question.type for question in loaded.questions]
    assert types.count("architecture") == 3
    assert types.count("implementation") == 4
    assert types.count("hybrid") == 3


def test_interview_cli_supports_interactive_custom_mix(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"
    inputs = "\n7\ny\n2\n2\n2\n2\n3\n2\n\nans1\nans2\nans3\nans4\nans5\nans6\nans7\n"

    result = runner.invoke(
        app,
        ["interview", "--session", str(session_path), "--out", str(out_path)],
        input=inputs,
    )

    assert result.exit_code == 0
    assert "请输入架构类题目数量：" in result.stdout
    assert "请输入实现类题目数量：" in result.stdout
    assert "请输入混合类题目数量：" in result.stdout
    assert "三类题目数量之和为 6，与总题数 7 不一致，请重新输入。" in result.stdout
    assert "是否开始？(Y/n)：" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert len(loaded.questions) == 7
    types = [question.type for question in loaded.questions]
    assert types.count("architecture") == 2
    assert types.count("implementation") == 3
    assert types.count("hybrid") == 2


def test_interview_cli_can_cancel_before_start(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report.md"

    result = runner.invoke(
        app,
        ["interview", "--session", str(session_path), "--out", str(out_path), "--num-questions", "6"],
        input="\nn\n",
    )

    assert result.exit_code == 0
    assert "是否开始？(Y/n)：" in result.stdout
    assert "已取消本次模拟面试。" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert loaded.questions == []
    assert loaded.qa_log == []


def test_interview_cli_supports_english_language_selection(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)
    out_path = tmp_path / "interview_report_en.md"
    inputs = "英文\n\nn\n\ny\na1\na2\na3\na4\na5\na6\n"

    result = runner.invoke(
        app,
        ["interview", "--session", str(session_path), "--out", str(out_path)],
        input=inputs,
    )

    assert result.exit_code == 0
    assert "请选择本次面试与报告语言（中文/英文，默认中文）：" in result.stdout
    assert "[Q1][Architecture]" in result.stdout
    assert "Your answer:" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert loaded.inputs["language"] == "en"
    assert loaded.questions[0].question.startswith("In project")
    report = out_path.read_text(encoding="utf-8")
    assert "# IC Mock Interview Report" in report
