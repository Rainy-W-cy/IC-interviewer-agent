"""Markdown report writer for interview sessions."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ic_interviewer.models import SessionState


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_NAME = "interview_report.md.j2"


def _build_overall_feedback(session: SessionState) -> dict[str, list[str] | str]:
    language = session.inputs.get("language", "zh")
    strengths: list[str] = []
    gaps: list[str] = []

    for qa_entry in session.qa_log:
        if qa_entry.evaluation:
            strengths.extend(qa_entry.evaluation.strengths[:1])
            gaps.extend(qa_entry.evaluation.gaps[:1])

    if language == "en":
        strengths = strengths[:3] or ["The candidate completed the baseline interview flow and could answer around project experience."]
        gaps = gaps[:3] or ["No critical weakness is obvious yet, but deeper technical follow-up is still needed."]
        if any("brief" in gap.lower() for gap in gaps):
            recommendation = "Follow up on implementation detail, debugging process, and design trade-offs."
        else:
            recommendation = "Probe further on corner cases, system trade-offs, and verification depth."
    else:
        strengths = strengths[:3] or ["候选人完成了基础问答，能够围绕项目给出回答。"]
        gaps = gaps[:3] or ["目前没有明显短板暴露，但还需要更深入的技术追问。"]
        if any("简略" in gap for gap in gaps):
            recommendation = "建议后续追问更多实现细节、调试过程和权衡依据。"
        else:
            recommendation = "建议进一步验证候选人在复杂边界条件和系统级权衡上的深度。"

    return {
        "strengths": strengths,
        "gaps": gaps,
        "recommendation": recommendation,
    }


def write_markdown_report(session: SessionState, out_path: str) -> None:
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template(TEMPLATE_NAME)
    overall_feedback = _build_overall_feedback(session)
    report_path = Path(out_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rendered = template.render(
        session=session,
        overall_feedback=overall_feedback,
        language=session.inputs.get("language", "zh"),
    )
    report_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")
