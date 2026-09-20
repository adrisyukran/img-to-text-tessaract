from pathlib import Path

import pytest

from backend.app.storage.workspaces import JobWorkspace


def test_workspace_creates_contained_job_directories(tmp_path: Path):
    workspace = JobWorkspace.create(tmp_path, "01ABC")
    assert workspace.root == tmp_path / "01ABC"
    assert (workspace.root / "input").is_dir()
    assert (workspace.root / "pages").is_dir()
    assert (workspace.root / "artifacts").is_dir()
    assert (workspace.root / "state").is_dir()


def test_workspace_sanitizes_input_name(tmp_path: Path):
    workspace = JobWorkspace.create(tmp_path, "01ABC")
    path = workspace.write_input("../escape.pdf", b"safe")
    assert path == workspace.root / "input" / "escape.pdf"
    assert path.read_bytes() == b"safe"


def test_workspace_rejects_unknown_artifact_key(tmp_path: Path):
    workspace = JobWorkspace.create(tmp_path, "01ABC")
    with pytest.raises(ValueError, match="unsupported artifact"):
        workspace.artifact_path("../../secret", "result.pdf")


def test_workspace_delete_does_not_touch_siblings(tmp_path: Path):
    workspace = JobWorkspace.create(tmp_path, "01ABC")
    sibling = tmp_path / "01SIBLING"
    sibling.mkdir()
    (sibling / "keep.txt").write_text("keep", encoding="utf-8")

    workspace.delete()

    assert not workspace.root.exists()
    assert (sibling / "keep.txt").exists()
