"""DOCX resume reader."""

from pathlib import Path

from docx import Document


def load_resume(path: str) -> dict[str, str]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Resume file not found: {source}")
    if not source.is_file():
        raise ValueError(f"Resume path is not a file: {source}")

    document = Document(source)
    raw_text = "\n".join(paragraph.text for paragraph in document.paragraphs)

    return {
        "source_path": str(source),
        "file_type": "docx",
        "raw_text": raw_text,
    }
