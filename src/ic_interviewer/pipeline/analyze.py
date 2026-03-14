"""Local-rule analyze pipeline."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from ic_interviewer.ingest import index_repo, load_resume
from ic_interviewer.models import Profile, ResumeData, ResumeProject, SessionState


SKILL_KEYWORDS = [
    "Python",
    "RISC-V",
    "AXI",
    "RTL",
    "Verilog",
    "SystemVerilog",
    "UVM",
    "scoreboard",
    "sequence",
    "STA",
    "PnR",
    "synthesis",
    "ADC",
    "PLL",
    "op-amp",
    "FPGA",
    "Zynq",
    "Vivado",
]

PROFILE_RULES = [
    (("risc-v", "axi", "rtl", "verilog"), "Digital IC / SoC", "Digital Design"),
    (("uvm", "scoreboard", "sequence"), "Digital IC / SoC", "Verification"),
    (("sta", "pnr", "synthesis"), "Backend / Physical Design", "Backend / Physical Design"),
    (("adc", "pll", "op-amp"), "Analog IC", "Analog IC"),
    (("fpga", "zynq", "vivado"), "FPGA", "FPGA"),
]


def extract_candidate_name(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    for line in lines[:5]:
        cleaned = re.sub(r"^[#>\-\*\d\.\)\s]+", "", line).strip()
        words = cleaned.split()
        if 2 <= len(words) <= 4 and all(any(ch.isalpha() for ch in word) for word in words):
            return cleaned
    return "Unknown Candidate"


def extract_skills(raw_text: str) -> list[str]:
    text_lower = raw_text.lower()
    skills = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in text_lower:
            skills.append(skill)
    return skills


def _clean_bullet(line: str) -> str:
    return re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", line).strip()


def _split_sections(raw_text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = re.sub(r"^[#]+", "", line).strip()
        is_markdown_heading = raw_line.lstrip().startswith("#")
        is_named_section = normalized.lower() in {"projects", "project experience", "experience"}
        is_upper_section = (
            not line.startswith(("-", "*", "•"))
            and normalized.replace(" ", "").isupper()
        )
        if len(normalized) <= 80 and (
            is_markdown_heading or is_upper_section or is_named_section
        ):
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = normalized
            current_lines = []
            continue

        if current_title is None:
            current_title = "General"
        current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, current_lines))
    return sections


def extract_projects(raw_text: str, skills: list[str]) -> list[ResumeProject]:
    sections = _split_sections(raw_text)
    projects: list[ResumeProject] = []

    for title, lines in sections:
        if "project" not in title.lower() and title != "General":
            continue

        current_name: str | None = None
        current_summary = ""
        current_claims: list[str] = []

        def flush() -> None:
            nonlocal current_name, current_summary, current_claims
            if not current_name:
                return
            claims = current_claims[:3]
            if not claims and current_summary:
                claims = [current_summary]
            keywords = [skill for skill in skills if skill.lower() in f"{current_name} {current_summary} {' '.join(claims)}".lower()]
            projects.append(
                ResumeProject(
                    name=current_name,
                    summary=current_summary or current_name,
                    claims=claims[:3],
                    keywords=keywords,
                )
            )
            current_name = None
            current_summary = ""
            current_claims = []

        for line in lines:
            cleaned = _clean_bullet(line)
            if not cleaned:
                continue
            is_heading = (
                line.lstrip().startswith(("-", "*", "•"))
                and len(cleaned.split()) <= 8
                and not cleaned.endswith(".")
            )
            if is_heading:
                flush()
                current_name = cleaned
                continue

            if current_name is None:
                current_name = cleaned[:80]
                continue

            if not current_summary:
                current_summary = cleaned
            if len(current_claims) < 3:
                current_claims.append(cleaned)

        flush()

    if projects:
        return projects

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    fallback_summary = lines[1] if len(lines) > 1 else "Resume content"
    fallback_claims = [_clean_bullet(line) for line in lines[1:4]]
    fallback_claims = [claim for claim in fallback_claims if claim][:3]
    return [
        ResumeProject(
            name="General Experience",
            summary=fallback_summary,
            claims=fallback_claims or [fallback_summary],
            keywords=skills[:5],
        )
    ]


def infer_profile(raw_text: str, skills: list[str], role: str | None = None) -> Profile:
    combined = " ".join([raw_text, " ".join(skills), role or ""]).lower()
    focus: list[str] = []
    reasons: list[str] = []
    industry = "General Hardware"

    for keywords, candidate_industry, candidate_focus in PROFILE_RULES:
        if any(keyword in combined for keyword in keywords):
            if industry == "General Hardware":
                industry = candidate_industry
            if candidate_focus not in focus:
                focus.append(candidate_focus)
            reasons.append(f"Matched keywords for {candidate_focus}: {', '.join(keywords)}")

    if not focus:
        focus = ["General Engineering"]
        reasons.append("No domain-specific keywords matched; using general engineering fallback.")

    secondary_focus = focus[1:]
    primary_focus = focus[:1]
    question_mix = {"project": 0.6, "fundamentals": 0.4}
    if "Verification" in focus:
        question_mix = {"project": 0.5, "verification": 0.5}

    return Profile(
        industry=industry,
        focus=primary_focus,
        secondary_focus=secondary_focus,
        question_mix=question_mix,
        reasons=reasons,
    )


def analyze_inputs(
    resume_path: str,
    session_path: str,
    repo_path: str | None = None,
    role: str | None = None,
) -> SessionState:
    resume_payload = load_resume(resume_path)
    raw_text = resume_payload["raw_text"]

    skills = extract_skills(raw_text)
    projects = extract_projects(raw_text, skills)
    resume = ResumeData(
        candidate_name=extract_candidate_name(raw_text),
        skills=skills,
        projects=projects,
    )
    profile = infer_profile(raw_text, skills, role=role)
    repo_index = {}
    if repo_path:
        indexed_repo = index_repo(repo_path)
        repo_index = {
            **indexed_repo,
            "indexed": True,
            "file_count": len(indexed_repo["files"]),
            "sample_files": indexed_repo["files"][:20],
            "repo_path": str(Path(repo_path)),
        }

    state = SessionState(
        session_id=f"session-{uuid4().hex[:12]}",
        inputs={
            "resume_path": resume_payload["source_path"],
            "repo_path": repo_path,
            "role": role or "",
            "file_type": resume_payload["file_type"],
        },
        resume=resume,
        profile=profile,
        repo_index=repo_index,
    )
    state.save_to_file(session_path)
    return state
