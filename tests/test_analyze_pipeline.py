from pathlib import Path

from typer.testing import CliRunner

from ic_interviewer.cli import app
from ic_interviewer.models import SessionState
from ic_interviewer.pipeline.analyze import analyze_inputs


def test_analyze_inputs_creates_session_with_rule_based_resume(tmp_path: Path) -> None:
    resume_path = tmp_path / "resume.md"
    session_path = tmp_path / "session.json"
    resume_path.write_text(
        "\n".join(
            [
                "# Alice Zhang",
                "",
                "Skills: RTL, Verilog, UVM, Python",
                "",
                "## Projects",
                "- RISC-V CPU",
                "Implemented a 5-stage RTL pipeline with AXI interface.",
                "Built UVM scoreboard and sequence library for verification.",
                "- FPGA Accelerator",
                "Prototyped on Zynq with Vivado.",
            ]
        ),
        encoding="utf-8",
    )

    state = analyze_inputs(str(resume_path), str(session_path), role="IC verification engineer")

    assert session_path.exists()
    assert state.resume is not None
    assert state.resume.candidate_name == "Alice Zhang"
    assert "RTL" in state.resume.skills
    assert len(state.resume.projects) >= 2
    assert 1 <= len(state.resume.projects[0].claims) <= 3
    assert state.profile is not None
    assert state.profile.industry == "Digital IC / SoC"
    assert "Digital Design" in state.profile.focus or "Verification" in state.profile.focus


def test_analyze_inputs_indexes_repo_when_provided(tmp_path: Path) -> None:
    resume_path = tmp_path / "resume.md"
    session_path = tmp_path / "session.json"
    repo_path = tmp_path / "candidate_repo"
    repo_path.mkdir()
    (repo_path / "rtl").mkdir()
    (repo_path / "rtl" / "top.sv").write_text("module top; endmodule", encoding="utf-8")
    resume_path.write_text("# Bob Li\n\nRTL Verilog UVM\n", encoding="utf-8")

    state = analyze_inputs(str(resume_path), str(session_path), repo_path=str(repo_path))

    assert state.repo_index["indexed"] is True
    assert state.repo_index["file_count"] == 1
    assert "rtl/top.sv" in state.repo_index["sample_files"]


def test_cli_analyze_writes_session_file(tmp_path: Path) -> None:
    runner = CliRunner()
    resume_path = tmp_path / "resume.md"
    session_path = tmp_path / "session.json"
    resume_path.write_text("# Carol Wu\n\nADC PLL op-amp\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "analyze",
            "--resume",
            str(resume_path),
            "--session",
            str(session_path),
        ],
    )

    assert result.exit_code == 0
    assert "Saved session to" in result.stdout
    loaded = SessionState.from_file(session_path)
    assert loaded.profile is not None
    assert loaded.profile.industry == "Analog IC"
