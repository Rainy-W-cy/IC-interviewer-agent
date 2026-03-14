"""CLI entrypoint for ic-interviewer."""

from pathlib import Path

import typer

from ic_interviewer.models import SessionState
from ic_interviewer.pipeline import analyze_inputs
from ic_interviewer.pipeline.interview import run_interview

app = typer.Typer(
    help="CLI for the ic-interviewer project.",
    no_args_is_help=True,
)


@app.command()
def init() -> None:
    """Initialize project state."""
    raise typer.Exit()


@app.command()
def analyze(
    resume: str = typer.Option(..., "--resume", help="Path to resume file."),
    session: str = typer.Option(..., "--session", help="Output session JSON path."),
    repo: str | None = typer.Option(None, "--repo", help="Optional repository path."),
    role: str | None = typer.Option(None, "--role", help="Optional target role text."),
) -> None:
    """Analyze resume inputs into a session file."""
    state = analyze_inputs(resume_path=resume, session_path=session, repo_path=repo, role=role)
    typer.echo(f"Saved session to {Path(session)}")
    typer.echo(f"Candidate: {state.resume.candidate_name if state.resume else 'unknown'}")


@app.command()
def inspect(
    session: str = typer.Option(..., "--session", help="Path to session JSON file."),
) -> None:
    """Inspect session state."""
    state = SessionState.from_file(session)

    typer.echo(f"会话ID: {state.session_id}")
    typer.echo(f"推断方向: {state.profile.industry if state.profile else ''}")
    typer.echo(
        "侧重点: "
        + ", ".join(
            (state.profile.focus + state.profile.secondary_focus) if state.profile else []
        )
    )
    typer.echo("推断依据:")
    for reason in state.profile.reasons if state.profile else []:
        typer.echo(f"- {reason}")

    typer.echo("项目列表:")
    for project in state.resume.projects if state.resume else []:
        typer.echo(f"- {project.name}: {project.summary}")

    typer.echo("仓库索引:")
    if state.repo_index:
        typer.echo(f"- 已索引: {state.repo_index.get('indexed', False)}")
        typer.echo(f"- 文件数量: {state.repo_index.get('file_count', 0)}")
        sample_files = state.repo_index.get("sample_files", [])
        typer.echo(f"- 示例文件: {', '.join(sample_files) if sample_files else ''}")
    else:
        typer.echo("- 已索引: False")


@app.command()
def confirm(
    session: str = typer.Option(..., "--session", help="要更新的会话文件路径。"),
    industry: str | None = typer.Option(None, "--industry", help="手动覆盖推断方向。"),
    focus: str | None = typer.Option(
        None,
        "--focus",
        help="多个侧重点用英文逗号分隔，例如：微架构,RTL实现",
    ),
) -> None:
    """Confirm or override derived session metadata."""
    state = SessionState.from_file(session)

    if state.profile is None:
        raise typer.BadParameter("Session does not contain a profile to confirm.")

    if industry:
        state.profile.industry = industry
    if focus is not None:
        focus_items = [item.strip() for item in focus.split(",") if item.strip()]
        state.profile.focus = focus_items[:1]
        state.profile.secondary_focus = focus_items[1:]

    state.confirmed = True
    state.save_to_file(session)
    typer.echo(f"已确认会话并保存: {Path(session)}")


@app.command()
def interview(
    session: str = typer.Option(..., "--session", help="Path to session JSON file."),
    out: str = typer.Option(..., "--out", help="Output path for updated interview session."),
    num_questions: int | None = typer.Option(
        None,
        "--num-questions",
        help="本次模拟面试的题目数量；不传时会在开始前交互式询问。",
    ),
    mix: str | None = typer.Option(
        None,
        "--mix",
        help="题型分布，例如：architecture=3,implementation=4,hybrid=3",
    ),
) -> None:
    """Run interactive interview flow."""
    state = run_interview(
        session_path=session,
        out_path=out,
        num_questions=num_questions,
        mix_text=mix,
    )
    typer.echo(f"Interview complete: {len(state.qa_log)} answers saved")



def main() -> None:
    app()


if __name__ == "__main__":
    main()
