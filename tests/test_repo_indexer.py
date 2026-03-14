from pathlib import Path

import pytest

from ic_interviewer.ingest.repo_indexer import index_repo


def test_index_repo_filters_files_and_extracts_symbols_and_topics(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "rtl").mkdir()
    (repo / "docs").mkdir()
    (repo / "scripts").mkdir()

    (repo / "rtl" / "top.sv").write_text(
        "module top;\nendmodule\nmodule hazard_unit;\nendmodule\n// axi forwarding stall\n",
        encoding="utf-8",
    )
    (repo / "rtl" / "defs.vh").write_text("// scoreboard\n", encoding="utf-8")
    (repo / "docs" / "notes.md").write_text("Pipeline and UVM scoreboard flow.\n", encoding="utf-8")
    (repo / "scripts" / "helper.py").write_text(
        "class RepoHelper:\n    pass\n\n\ndef build_index():\n    return 'uvm'\n",
        encoding="utf-8",
    )
    (repo / "ignore.bin").write_bytes(b"\x00\x01")

    result = index_repo(str(repo))

    assert result["files"] == [
        "docs/notes.md",
        "rtl/defs.vh",
        "rtl/top.sv",
        "scripts/helper.py",
    ]
    assert "rtl/top.sv:top" in result["symbols"]
    assert "rtl/top.sv:hazard_unit" in result["symbols"]
    assert "scripts/helper.py:RepoHelper" in result["symbols"]
    assert "scripts/helper.py:build_index" in result["symbols"]
    assert result["topics"] == ["axi", "forwarding", "hazard", "pipeline", "scoreboard", "stall", "uvm"]


def test_index_repo_raises_clear_error_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing_repo"

    with pytest.raises(FileNotFoundError, match="Repository path not found"):
        index_repo(str(missing))


def test_index_repo_raises_clear_error_for_file_input(tmp_path: Path) -> None:
    not_dir = tmp_path / "file.md"
    not_dir.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="Repository path is not a directory"):
        index_repo(str(not_dir))
