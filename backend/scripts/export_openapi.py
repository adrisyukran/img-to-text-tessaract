from __future__ import annotations

import json
from pathlib import Path

from backend.app.main import app


def main() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    output_path = repository_root / "frontend" / "openapi.json"
    output_path.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
