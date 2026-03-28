"""Check non-top-level (runtime) imports in NcatBot source code.

Scans all ``.py`` files under ``ncatbot/`` and classifies every import that
is NOT at module top-level into one of:

- **TYPE_CHECKING** — inside ``if TYPE_CHECKING:`` guard (safe, skip)
- **function_body** — inside a function / method body
- **try_except** — inside a ``try/except`` block
- **runtime_if** — inside an ``if`` that is NOT ``TYPE_CHECKING``

For ``function_body`` imports, the script further classifies them as:

- **optional_dep** — third-party optional dependency that may not be installed
  (bilibili_api, litellm, etc.)
- **cli_lazy** — inside ``cli/`` Click command function (startup perf)
- **same_module_lazy** — relative import within the same top-level layer
- **cycle_breaker** — ``ncatbot.*`` cross-layer deferred import
- **stdlib_lazy** — deferred stdlib import
- **other** — anything else

Usage::

    python .agents/scripts/check_runtime_imports.py            # summary + per-file details
    python .agents/scripts/check_runtime_imports.py --stat     # summary only
    python .agents/scripts/check_runtime_imports.py --strict   # summary + details; exit 1 if violations

Exit code:
    0 — no actionable runtime imports (or ``--stat``).
    1 — (``--strict``) actionable runtime imports found.
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Third-party packages that are optional / may not be installed.
# Imports of these inside function bodies are expected and only noted.
OPTIONAL_DEPS: set[str] = {
    "bilibili_api",
    "litellm",
    "schedule",
}

# Top-level layers (for classifying cross vs. intra-layer)
LAYERS: set[str] = {
    "adapter",
    "api",
    "app",
    "cli",
    "core",
    "event",
    "plugin",
    "service",
    "testing",
    "types",
    "utils",
}

SCAN_DIR = "ncatbot"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Cannot find project root")


_root = _find_root()


def _posix(p: Path) -> str:
    return str(p.relative_to(_root)).replace("\\", "/")


def _layer_of(rel: str) -> str | None:
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "ncatbot" and parts[1] in LAYERS:
        return parts[1]
    return None


# ---------------------------------------------------------------------------
# AST analysis
# ---------------------------------------------------------------------------


def _type_checking_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    """Return ``(start, end)`` line ranges for ``if TYPE_CHECKING:`` blocks."""
    ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        is_tc = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
            isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
        )
        if is_tc:
            start = node.lineno
            end = max(getattr(n, "lineno", start) for n in ast.walk(node))
            ranges.append((start, end))
    return ranges


def _in_tc(lineno: int, tc: list[tuple[int, int]]) -> bool:
    return any(s <= lineno <= e for s, e in tc)


def _classify_top_level(
    node: ast.AST, tree: ast.Module, tc: list[tuple[int, int]]
) -> str | None:
    """Return a classification string for a non-top-level import, or None if top-level."""
    lineno = getattr(node, "lineno", 0)

    for stmt in tree.body:
        if stmt is node:
            return None  # genuine top-level

        if isinstance(stmt, ast.If):
            for child in ast.walk(stmt):
                if child is node:
                    if _in_tc(lineno, tc):
                        return "TYPE_CHECKING"
                    if _is_platform_guard(stmt):
                        return "platform_guard"
                    return "runtime_if"

        if isinstance(stmt, (ast.Try, ast.TryStar)):
            for child in ast.walk(stmt):
                if child is node:
                    return "try_except"

    return "function_body"


def _is_platform_guard(if_node: ast.If) -> bool:
    """Return True if the ``if`` node tests ``sys.platform``."""
    test = if_node.test
    # sys.platform == "win32"  /  sys.platform != "linux"
    if isinstance(test, ast.Compare):
        left = test.left
        if isinstance(left, ast.Attribute) and left.attr == "platform":
            if isinstance(left.value, ast.Name) and left.value.id == "sys":
                return True
    # sys.platform (bare truthy check, unlikely but safe)
    if isinstance(test, ast.Attribute) and test.attr == "platform":
        if isinstance(test.value, ast.Name) and test.value.id == "sys":
            return True
    return False


def _import_module(node: ast.AST) -> str:
    """Extract the module string from an import node."""
    if isinstance(node, ast.ImportFrom):
        return node.module or ""
    # ast.Import
    return ", ".join(a.name for a in node.names)


def _import_stmt(node: ast.AST, source: str) -> str:
    seg = ast.get_source_segment(source, node)
    if seg:
        first_line = seg.split("\n")[0]
        return first_line if len(first_line) <= 100 else first_line[:97] + "..."
    if isinstance(node, ast.ImportFrom):
        names = ", ".join(a.name for a in node.names)
        return f"from {node.module} import {names}"
    return f"import {_import_module(node)}"


# ---------------------------------------------------------------------------
# Sub-classification for function_body imports
# ---------------------------------------------------------------------------


def _sub_classify(mod: str, file_rel: str) -> str:
    """Sub-classify a function-body import."""
    # Optional third-party dep
    for pkg in OPTIONAL_DEPS:
        if mod == pkg or mod.startswith(pkg + "."):
            return "optional_dep"

    # CLI lazy loading
    if file_rel.startswith("ncatbot/cli/"):
        return "cli_lazy"

    # ncatbot internal import
    if mod.startswith("ncatbot."):
        src_layer = _layer_of(file_rel)
        parts = mod.split(".")
        target_layer = parts[1] if len(parts) >= 2 else None
        if src_layer and target_layer == src_layer:
            return "same_module_lazy"
        return "cycle_breaker"

    # Relative import (level > 0) — intra-module
    if not mod:
        return "same_module_lazy"

    # stdlib / other third-party
    # Simple heuristic: if the module exists in stdlib, mark it
    try:
        import importlib.util

        spec = importlib.util.find_spec(mod.split(".")[0])
        if spec and spec.origin and "site-packages" not in (spec.origin or ""):
            return "stdlib_lazy"
    except (ModuleNotFoundError, ValueError):
        pass

    return "other"


# ---------------------------------------------------------------------------
# Entry: Dataclass
# ---------------------------------------------------------------------------


class RuntimeImport:
    __slots__ = ("file", "line", "stmt", "module", "category", "sub")

    def __init__(
        self, file: str, line: int, stmt: str, module: str, category: str, sub: str = ""
    ):
        self.file = file
        self.line = line
        self.stmt = stmt
        self.module = module
        self.category = category
        self.sub = sub


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def scan(root: Path) -> list[RuntimeImport]:
    results: list[RuntimeImport] = []
    scan_dir = root / SCAN_DIR

    for py_file in sorted(scan_dir.rglob("*.py")):
        rel = _posix(py_file)
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        tc = _type_checking_ranges(tree)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue

            cat = _classify_top_level(node, tree, tc)
            if cat is None:
                continue  # top-level, skip

            mod = _import_module(node)
            stmt = _import_stmt(node, source)
            sub = ""

            if cat == "function_body":
                # Resolve relative imports for sub-classification
                resolved_mod = mod
                if isinstance(node, ast.ImportFrom) and node.level > 0:
                    # Relative import inside cli/ → cli_lazy
                    if rel.startswith("ncatbot/cli/"):
                        sub = "cli_lazy"
                    else:
                        sub = "same_module_lazy"
                else:
                    sub = _sub_classify(resolved_mod, rel)

            results.append(RuntimeImport(rel, node.lineno, stmt, mod, cat, sub))

    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


_CAT_LABELS = {
    "TYPE_CHECKING": "TYPE_CHECKING (safe)",
    "function_body": "Function body",
    "try_except": "Try/except",
    "runtime_if": "Runtime if-guard",
    "platform_guard": "平台条件导入 (仅提示)",
}

_SUB_LABELS = {
    "optional_dep": "可选第三方依赖 (仅提示)",
    "cli_lazy": "CLI 懒加载 (仅提示)",
    "same_module_lazy": "同层内部懒加载 (仅提示)",
    "cycle_breaker": "⚠️  跨层延迟导入 (应移至顶层)",
    "stdlib_lazy": "标准库延迟导入 (应移至顶层)",
    "other": "其他延迟导入",
}

# Categories considered "info only" — not actionable
INFO_SUBS = {"optional_dep", "cli_lazy", "same_module_lazy"}


def report(results: list[RuntimeImport], *, stat_only: bool = False) -> int:
    """Print report. Return count of actionable items."""
    by_cat: dict[str, list[RuntimeImport]] = defaultdict(list)
    for r in results:
        by_cat[r.category].append(r)

    total = len(results)
    tc_count = len(by_cat.get("TYPE_CHECKING", []))

    print(f"非顶层导入总数: {total}")
    print(f"  TYPE_CHECKING: {tc_count} (安全)")
    print(f"  function_body: {len(by_cat.get('function_body', []))}")
    print(f"  try_except:    {len(by_cat.get('try_except', []))}")
    print(f"  runtime_if:    {len(by_cat.get('runtime_if', []))}")
    print(f"  platform_guard:{len(by_cat.get('platform_guard', []))}")
    print()

    # --- function_body sub-classification summary ---
    fb = by_cat.get("function_body", [])
    by_sub: dict[str, list[RuntimeImport]] = defaultdict(list)
    for r in fb:
        by_sub[r.sub].append(r)

    if fb:
        print("── function_body 子分类汇总 ──")
        for sub_key in (
            "optional_dep",
            "cli_lazy",
            "same_module_lazy",
            "cycle_breaker",
            "stdlib_lazy",
            "other",
        ):
            items = by_sub.get(sub_key, [])
            if items:
                label = _SUB_LABELS.get(sub_key, sub_key)
                print(f"  {label}: {len(items)}")
        print()

    # --- Actionable count (for --strict exit code) ---
    actionable_subs = ("cycle_breaker", "stdlib_lazy", "other")
    actionable = []
    for sub_key in actionable_subs:
        actionable.extend(by_sub.get(sub_key, []))
    for cat in ("try_except", "runtime_if"):
        actionable.extend(by_cat.get(cat, []))

    if stat_only:
        if actionable:
            print(f"❌  发现 {len(actionable)} 个需要处理的运行时导入")
        else:
            print("✅  无需处理的运行时导入")
        return len(actionable)

    # --- 按文件输出所有运行时导入（排除 TYPE_CHECKING 和 optional_dep）---
    visible = [
        r
        for r in results
        if r.category not in ("TYPE_CHECKING",) and r.sub != "optional_dep"
    ]

    if visible:
        print("=" * 72)
        print("运行时导入明细 (排除 TYPE_CHECKING / 可选第三方依赖)")
        print("=" * 72)

        by_file: dict[str, list[RuntimeImport]] = defaultdict(list)
        for r in visible:
            by_file[r.file].append(r)

        for fpath in sorted(by_file):
            print(f"\n  {fpath}")
            for r in sorted(by_file[fpath], key=lambda x: x.line):
                tag = r.sub or r.category
                label = _SUB_LABELS.get(tag, _CAT_LABELS.get(tag, tag))
                marker = (
                    " ⚠️"
                    if tag
                    in (
                        "cycle_breaker",
                        "stdlib_lazy",
                        "other",
                        "try_except",
                        "runtime_if",
                    )
                    else ""
                )
                print(f"    L{r.line:<5} [{tag}]  {r.stmt}{marker}")

    # --- Summary ---
    print()
    if actionable:
        print(f"❌  发现 {len(actionable)} 个需要处理的运行时导入")
    else:
        print("✅  无需处理的运行时导入")

    return len(actionable)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    stat_only = "--stat" in sys.argv
    strict = "--strict" in sys.argv

    results = scan(_root)
    count = report(results, stat_only=stat_only)

    if strict and count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
