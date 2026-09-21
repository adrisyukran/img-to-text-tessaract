from pathlib import Path


def test_docker_entrypoint_uses_lf_line_endings() -> None:
    entrypoint = Path(__file__).parents[2] / "docker" / "entrypoint.sh"
    content = entrypoint.read_bytes()

    assert content.startswith(b"#!/bin/sh\n")
    assert b"\r\n" not in content


def test_compose_api_host_port_is_configurable() -> None:
    compose_file = Path(__file__).parents[2] / "compose.yaml"
    compose = compose_file.read_text(encoding="utf-8")

    assert '- "${OCR_HTTP_PORT:-8000}:8000"' in compose
