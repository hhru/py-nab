import os
import pathlib
import subprocess


ROOT = str(pathlib.Path(os.path.dirname(__file__)).parent)


def test_ruff() -> None:
    subprocess.run(
        ["ruff", "./ararat", "./tests"],
        cwd=ROOT,
    ).check_returncode()
    subprocess.run(
        ["ruff", "format", "--check", "./ararat", "./tests"],
        cwd=ROOT,
    ).check_returncode()
