import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_PATHS = ("src", "tests")


def _run_check(executable: str, *args: str) -> None:
    tool = shutil.which(executable)
    assert tool is not None, (
        f"{executable} is not installed. Run `uv sync --dev` before running pytest."
    )

    result = subprocess.run(
        [tool, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    assert result.returncode == 0, output or f"{executable} exited with {result.returncode}"


def test_ruff_passes() -> None:
    _run_check("ruff", "check", *CHECK_PATHS)


def test_pyright_passes() -> None:
    _run_check("pyright", *CHECK_PATHS)
