"""Runtime shim to support `python -m ic_interviewer.cli` from the repo root."""

from pathlib import Path

_src_pkg = Path(__file__).resolve().parent.parent / "src" / "ic_interviewer"
__path__ = [str(_src_pkg)]
