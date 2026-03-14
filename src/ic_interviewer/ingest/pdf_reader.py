"""PDF resume reader."""

from pathlib import Path

from pypdf import PdfReader


def load_resume(path: str) -> dict[str, str]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Resume file not found: {source}")
    if not source.is_file():
        raise ValueError(f"Resume path is not a file: {source}")

    reader = PdfReader(str(source))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return {
        "source_path": str(source),
        "file_type": "pdf",
        "raw_text": "\n".join(pages).strip(),
    }
