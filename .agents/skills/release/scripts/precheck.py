"""Local precheck: lint + format + test with auto-fix and report.

Usage (from project root):
    uv run python .agents/skills/release/scripts/precheck.py
"""

import subprocess
import sys
from pathlib import Path

# ── 项目根目录 ────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[4]  # .agents/skills/release/scripts -> root

# ── 工具函数 ──────────────────────────────────────────────


def _run(args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """在项目根目录执行命令，返回 CompletedProcess。"""
    kwargs: dict = dict(cwd=ROOT, text=True)
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return subprocess.run(args, **kwargs)  # noqa: S603


def _header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _result_line(label: str, ok: bool, detail: str = "") -> str:
    icon = "PASS" if ok else "FAIL"
    line = f"  [{icon}]  {label}"
    if detail:
        line += f"  ({detail})"
    return line


# ── 步骤 ─────────────────────────────────────────────────


def step_lint() -> tuple[bool, str]:
    """Ruff lint：先 --fix 再验证残余错误。"""
    _header("1/3  Ruff Lint (--fix)")
    _run(["uv", "run", "ruff", "check", "--fix", "."])
    result = _run(["uv", "run", "ruff", "check", "."], capture=True)
    if result.returncode == 0:
        return True, "clean"
    print(result.stdout)
    return False, "errors remain, manual fix needed"


def step_format() -> tuple[bool, str]:
    """Ruff format：先自动格式化再验证。"""
    _header("2/3  Ruff Format (auto)")
    _run(["uv", "run", "ruff", "format", "."])
    result = _run(["uv", "run", "ruff", "format", "--check", "."], capture=True)
    if result.returncode == 0:
        return True, "consistent"
    print(result.stdout)
    return False, "format diff remains"


def step_test() -> tuple[bool, str]:
    """Pytest --no-cov。"""
    _header("3/3  Pytest (--no-cov)")
    result = _run(["uv", "run", "pytest", "--no-cov"], capture=True)
    print(result.stdout)
    # 从输出中提取摘要行
    summary = ""
    for line in reversed(result.stdout.splitlines()):
        if "passed" in line or "failed" in line or "error" in line:
            summary = line.strip()
            break
    return result.returncode == 0, summary or f"exit {result.returncode}"


# ── 主流程 ────────────────────────────────────────────────


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    for label, step_fn in [
        ("Ruff Lint", step_lint),
        ("Ruff Format", step_format),
        ("Pytest", step_test),
    ]:
        ok, detail = step_fn()
        results.append((label, ok, detail))

    # report
    _header("Precheck Report")
    all_ok = True
    for label, ok, detail in results:
        print(_result_line(label, ok, detail))
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("  All passed -- safe to push")
    else:
        print("  Some checks failed -- fix and re-run")
    print()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
