"""Minimal repository indexer based on file and regex scanning."""

from __future__ import annotations

import re
from pathlib import Path


SUPPORTED_SUFFIXES = {".sv", ".v", ".vh", ".md", ".txt", ".py"}
TOPIC_KEYWORDS = ["pipeline", "hazard", "forwarding", "stall", "axi", "uvm", "scoreboard"]

SV_MODULE_RE = re.compile(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)")
PY_CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)
PY_DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _extract_symbols(relative_path: str, suffix: str, content: str) -> list[str]:
    symbols: list[str] = []
    if suffix in {".sv", ".v"}:
        symbols.extend(match.group(1) for match in SV_MODULE_RE.finditer(content))
    elif suffix == ".py":
        symbols.extend(match.group(1) for match in PY_CLASS_RE.finditer(content))
        symbols.extend(match.group(1) for match in PY_DEF_RE.finditer(content))

    return [f"{relative_path}:{symbol}" for symbol in symbols]


def _extract_topics(content: str) -> list[str]:
    lowered = content.lower()
    return [topic for topic in TOPIC_KEYWORDS if topic in lowered]


def index_repo(repo_path: str) -> dict[str, list[str]]:
    repo = Path(repo_path)
    if not repo.exists():
        raise FileNotFoundError(f"Repository path not found: {repo}")
    if not repo.is_dir():
        raise ValueError(f"Repository path is not a directory: {repo}")

    files: list[str] = []
    symbols: list[str] = []
    topics: set[str] = set()

    for path in sorted(repo.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        relative_path = str(path.relative_to(repo))
        files.append(relative_path)

        content = _read_text(path)
        symbols.extend(_extract_symbols(relative_path, path.suffix.lower(), content))
        topics.update(_extract_topics(content))

    return {
        "files": files,
        "symbols": symbols,
        "topics": sorted(topics),
    }
