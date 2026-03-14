"""Core data models for the interview pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field


class FileModel(BaseModel):
    """Shared helpers for reading and writing JSON-backed models."""

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_file(cls, path: str | Path) -> Self:
        data = Path(path).read_text(encoding="utf-8")
        return cls.model_validate_json(data)

    def save_to_file(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)


class ResumeProject(FileModel):
    name: str
    summary: str
    claims: list[str]
    keywords: list[str]


class ResumeData(FileModel):
    candidate_name: str
    skills: list[str]
    projects: list[ResumeProject]


class Profile(FileModel):
    industry: str
    focus: list[str]
    secondary_focus: list[str] = Field(default_factory=list)
    question_mix: dict[str, float]
    reasons: list[str]


class Question(FileModel):
    id: str
    type: str
    project: str
    topic: str
    question: str


class Evaluation(FileModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    anchors: list[str]
    standard_answer: str
    memorization_answer: str


class QALog(FileModel):
    question: Question
    answer: str
    evaluation: Evaluation | None = None


class SessionState(FileModel):
    session_id: str
    inputs: dict[str, Any]
    resume: ResumeData | None = None
    profile: Profile | None = None
    confirmed: bool = False
    repo_index: dict[str, Any] = Field(default_factory=dict)
    questions: list[Question] = Field(default_factory=list)
    qa_log: list[QALog] = Field(default_factory=list)
    report_path: str = ""
