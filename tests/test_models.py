from ic_interviewer.models import (
    Evaluation,
    Profile,
    QALog,
    Question,
    ResumeData,
    ResumeProject,
    SessionState,
)


def test_resume_data_round_trip(tmp_path) -> None:
    resume = ResumeData(
        candidate_name="Alice",
        skills=["Python", "RTL"],
        projects=[
            ResumeProject(
                name="IC Debugger",
                summary="Built a debug tool.",
                claims=["Improved throughput"],
                keywords=["python", "eda"],
            )
        ],
    )

    path = tmp_path / "resume.json"
    resume.save_to_file(path)
    loaded = ResumeData.from_file(path)

    assert loaded == resume
    assert loaded.projects[0].name == "IC Debugger"


def test_session_state_defaults_and_nested_models(tmp_path) -> None:
    question = Question(
        id="q-1",
        type="project",
        project="IC Debugger",
        topic="verification",
        question="How did you validate correctness?",
    )
    evaluation = Evaluation(
        summary="Solid answer.",
        strengths=["clear metrics"],
        gaps=["limited edge cases"],
        anchors=["throughput"],
        standard_answer="Discuss validation strategy.",
        memorization_answer="Repeat prepared summary.",
    )
    qa_log = QALog(question=question, answer="I used regression suites.", evaluation=evaluation)
    profile = Profile(
        industry="semiconductor",
        focus=["verification"],
        question_mix={"project": 0.7, "fundamentals": 0.3},
        reasons=["Resume emphasizes verification work."],
    )

    state = SessionState(
        session_id="session-1",
        inputs={"resume_path": "resume.md"},
        profile=profile,
        questions=[question],
        qa_log=[qa_log],
    )

    assert state.confirmed is False
    assert state.repo_index == {}
    assert state.report_path == ""
    assert profile.secondary_focus == []

    path = tmp_path / "state.json"
    state.save_to_file(path)
    loaded = SessionState.from_file(path)

    assert loaded == state
    assert loaded.qa_log[0].evaluation is not None
    assert loaded.qa_log[0].evaluation.summary == "Solid answer."
