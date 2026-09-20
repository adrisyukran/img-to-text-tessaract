import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ARTIFACT_NAMES: Final[dict[str, str]] = {
    "document_json": "document.json",
    "document_markdown": "document.md",
    "document_html": "document.html",
    "document_docx": "document.docx",
    "searchable_pdf": "searchable.pdf",
    "report_json": "report.json",
}


def _safe_basename(filename: str) -> str:
    candidate = Path(filename.replace("\\", "/")).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate).strip("._")
    return cleaned or "document"


@dataclass(frozen=True)
class JobWorkspace:
    root: Path

    @classmethod
    def create(cls, root: Path, job_id: str) -> "JobWorkspace":
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", job_id):
            raise ValueError("invalid job id")
        resolved_root = root.resolve() / job_id
        resolved_root.mkdir(parents=True, exist_ok=False)
        for name in ("input", "pages", "artifacts", "state"):
            (resolved_root / name).mkdir()
        return cls(resolved_root)

    @property
    def input_dir(self) -> Path:
        return self.root / "input"

    @property
    def pages_dir(self) -> Path:
        return self.root / "pages"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    def _contained(self, candidate: Path) -> Path:
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root.resolve()):
            raise ValueError("path escapes job workspace")
        return resolved

    def write_input(self, filename: str, content: bytes) -> Path:
        target = self._contained(self.input_dir / _safe_basename(filename))
        with target.open("xb") as stream:
            stream.write(content)
        return target

    def artifact_path(self, key: str, filename: str | None = None) -> Path:
        if key not in ARTIFACT_NAMES:
            raise ValueError(f"unsupported artifact: {key}")
        candidate = self.artifacts_dir / (filename or ARTIFACT_NAMES[key])
        return self._contained(candidate)

    def delete(self) -> None:
        resolved_root = self.root.resolve()
        if resolved_root.parent == resolved_root or len(resolved_root.parts) < 2:
            raise ValueError("refusing to delete unsafe workspace")
        if resolved_root.exists():
            shutil.rmtree(resolved_root)
