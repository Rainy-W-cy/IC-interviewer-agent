from pathlib import Path

from typer.testing import CliRunner

from ic_interviewer.cli import app
from ic_interviewer.models import Profile, ResumeData, ResumeProject, SessionState


def make_session(tmp_path: Path) -> Path:
    session_path = tmp_path / "session.json"
    state = SessionState(
        session_id="session-123",
        inputs={"resume_path": "resume.md"},
        resume=ResumeData(
            candidate_name="Alice",
            skills=["RTL", "UVM"],
            projects=[
                ResumeProject(
                    name="RISC-V CPU",
                    summary="Implemented a CPU pipeline.",
                    claims=["Built RTL", "Added AXI bus"],
                    keywords=["RTL", "AXI"],
                )
            ],
        ),
        profile=Profile(
            industry="Digital IC / SoC",
            focus=["Verification"],
            secondary_focus=["Digital Design"],
            question_mix={"project": 0.5, "verification": 0.5},
            reasons=["Matched keywords for Verification: uvm, scoreboard, sequence"],
        ),
        repo_index={"indexed": True, "file_count": 3, "sample_files": ["rtl/top.sv"]},
    )
    state.save_to_file(session_path)
    return session_path


def test_inspect_prints_session_summary(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)

    result = runner.invoke(app, ["inspect", "--session", str(session_path)])

    assert result.exit_code == 0
    assert "会话ID: session-123" in result.stdout
    assert "推断方向: Digital IC / SoC" in result.stdout
    assert "侧重点: Verification, Digital Design" in result.stdout
    assert "推断依据:" in result.stdout
    assert "Matched keywords for Verification" in result.stdout
    assert "项目列表:" in result.stdout
    assert "RISC-V CPU: Implemented a CPU pipeline." in result.stdout
    assert "仓库索引:" in result.stdout
    assert "文件数量: 3" in result.stdout


def test_confirm_overrides_profile_and_marks_confirmed(tmp_path: Path) -> None:
    runner = CliRunner()
    session_path = make_session(tmp_path)

    result = runner.invoke(
        app,
        [
            "confirm",
            "--session",
            str(session_path),
            "--industry",
            "FPGA",
            "--focus",
            "FPGA,Acceleration",
        ],
    )

    assert result.exit_code == 0
    assert "已确认会话并保存:" in result.stdout

    state = SessionState.from_file(session_path)
    assert state.confirmed is True
    assert state.profile is not None
    assert state.profile.industry == "FPGA"
    assert state.profile.focus == ["FPGA"]
    assert state.profile.secondary_focus == ["Acceleration"]
