"""Markdown resume reader."""

from pathlib import Path


def load_resume(path: str) -> dict[str, str]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Resume file not found: {source}")
    if not source.is_file():
        raise ValueError(f"Resume path is not a file: {source}")

    return {
        "source_path": str(source),
        "file_type": "md",
        "raw_text": source.read_text(encoding="utf-8"),
    }
