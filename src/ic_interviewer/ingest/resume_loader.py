"""Unified resume loader."""

from pathlib import Path

from . import docx_reader, md_reader, pdf_reader


def load_resume(path: str) -> dict[str, str]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Resume file not found: {source}")
    if not source.is_file():
        raise ValueError(f"Resume path is not a file: {source}")

    suffix = source.suffix.lower()
    if suffix == ".pdf":
        return pdf_reader.load_resume(str(source))
    if suffix == ".docx":
        return docx_reader.load_resume(str(source))
    if suffix == ".md":
        return md_reader.load_resume(str(source))

    raise ValueError(
        f"Unsupported resume format: {source.suffix or '<no extension>'}. "
        "Supported formats are: .pdf, .docx, .md"
    )
