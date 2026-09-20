from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def test_static_mount_is_allowlisted_and_has_security_headers(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><main>app</main>", encoding="utf-8")
    (dist / "assets").mkdir()
    (dist / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    settings = Settings(environment="test", workspace_root=tmp_path, frontend_dist=dist)

    with TestClient(create_app(settings, enqueue_job=lambda job_id: None)) as client:
        home = client.get("/")
        spa = client.get("/jobs/demo")
        dotfile = client.get("/.env")
        legacy = client.get("/server.js")
        asset = client.get("/assets/app.js")

    assert home.status_code == 200
    assert spa.status_code == 200
    assert dotfile.status_code == 404
    assert legacy.status_code == 404
    assert asset.status_code == 200
    assert "default-src 'self'" in home.headers["content-security-policy"]
    assert home.headers["x-content-type-options"] == "nosniff"
