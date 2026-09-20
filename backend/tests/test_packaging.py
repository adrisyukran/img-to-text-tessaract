from pathlib import Path


def test_docker_entrypoint_uses_lf_line_endings() -> None:
    entrypoint = Path(__file__).parents[2] / "docker" / "entrypoint.sh"
    content = entrypoint.read_bytes()

    assert content.startswith(b"#!/bin/sh\n")
    assert b"\r\n" not in content
