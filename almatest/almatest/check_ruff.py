from __future__ import annotations
import subprocess


def check_ruff(root: str, paths: list[str]):
    subprocess.run(["ruff"] + paths, cwd=root).check_returncode()
    subprocess.run(["ruff", "format", "--check"] + paths, cwd=root).check_returncode()
