from typer.testing import CliRunner

from ic_interviewer.cli import app


def test_help_renders() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "analyze" in result.stdout
