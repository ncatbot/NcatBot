"""Check NcatBot import conventions.

Rules:
  1. Cross-layer absolute imports max 2 levels: ``from ncatbot.<layer> import ...``
     or ``from ncatbot.<layer>.<platform> import ...`` (whitelisted platform submodules).
  2. Same-layer internal imports must use relative imports.

Exceptions:
  - ``if TYPE_CHECKING:`` blocks are skipped.
  - Private implementation access (path segments starting with ``_``) is allowed.
  - CLI runtime lazy imports inside functions in ``cli/`` are allowed for adapter internals.

Usage::

    python dev/check_imports.py          # report violations
    python dev/check_imports.py --stat   # summary only
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LAYERS = {
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

# Layers that allow 2-level (platform sub-module) cross-layer imports.
# Mapping: layer -> set of allowed sub-module names.
# ``"*"`` means any sub-module is allowed (dynamic platforms).
PLATFORM_LAYERS: dict[str, str | set[str]] = {
    "event": "*",
    "types": "*",
    "api": "*",
    "adapter": "*",
}

# CLI lazy-import whitelist: files whose *function-level* imports from
# adapter internals are exempt from the depth rule.
CLI_EXEMPT_FILES = {
    "ncatbot/cli/commands/napcat.py",
    "ncatbot/cli/commands/adapter.py",
}

# Directories to scan
SCAN_DIRS_PY = [
    "ncatbot",
    "plugins",
    "docs/docs/examples",
]

SCAN_DIRS_MD = [
    ".agents/skills",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_root() -> Path:
    """向上查找含 pyproject.toml 的目录作为项目根。"""
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Cannot find project root (no pyproject.toml found)")


_root = _find_root()


def _posix(p: Path) -> str:
    return str(p.relative_to(_root)).replace("\\", "/")


def _layer_of_file(rel: str) -> str | None:
    """Return the layer name for a file path like ``ncatbot/<layer>/...``."""
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "ncatbot" and parts[1] in LAYERS:
        return parts[1]
    return None


def _parse_import_module(node: ast.ImportFrom) -> str | None:
    """Return the full module string for a ``from X import ...`` node."""
    if node.module is None:
        return None
    return node.module


def _is_relative(node: ast.ImportFrom) -> bool:
    return node.level > 0


def _is_ncatbot_import(module: str) -> bool:
    return module.startswith("ncatbot.")


def _split_ncatbot(module: str) -> list[str]:
    """Split ``ncatbot.core.registry.foo`` → [``core``, ``registry``, ``foo``]."""
    return module.split(".")[1:]  # drop ``ncatbot``


def _has_private_segment(parts: list[str]) -> bool:
    return any(p.startswith("_") for p in parts)


def _depth(parts: list[str]) -> int:
    """Import depth after ``ncatbot``.  ``ncatbot.core`` → 1, ``ncatbot.core.foo`` → 2."""
    return len(parts)


def _is_platform_2level_ok(layer: str, sub: str) -> bool:
    """Check if ``ncatbot.<layer>.<sub>`` is a whitelisted 2-level import."""
    if layer not in PLATFORM_LAYERS:
        return False
    allowed = PLATFORM_LAYERS[layer]
    if allowed == "*":
        return True
    return sub in allowed  # type: ignore[operator]


# ---------------------------------------------------------------------------
# AST-based checker for .py files
# ---------------------------------------------------------------------------


class Violation:
    def __init__(self, file: str, line: int, stmt: str, rule: str, detail: str):
        self.file = file
        self.line = line
        self.stmt = stmt
        self.rule = rule
        self.detail = detail

    def __str__(self) -> str:
        return f"  {self.file}:{self.line}  [{self.rule}]  {self.stmt}\n    → {self.detail}"


def _in_type_checking(node: ast.AST, type_check_ranges: list[tuple[int, int]]) -> bool:
    lineno = getattr(node, "lineno", 0)
    return any(start <= lineno <= end for start, end in type_check_ranges)


def _find_type_checking_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    """Find line ranges of ``if TYPE_CHECKING:`` blocks."""
    ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_tc = False
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                is_tc = True
            elif isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                is_tc = True
            if is_tc:
                start = node.lineno
                end = max(getattr(n, "lineno", start) for n in ast.walk(node))
                ranges.append((start, end))
    return ranges


def _is_in_function(node: ast.ImportFrom, tree: ast.Module) -> bool:
    """Check if an import node is inside a function/method body."""
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(parent):
                if child is node:
                    return True
    return False


def check_py_file(filepath: Path) -> list[Violation]:
    violations: list[Violation] = []
    rel = _posix(filepath)
    src_layer = _layer_of_file(rel)

    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    tc_ranges = _find_type_checking_ranges(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue

        # Skip relative imports for Rule 1 check, but check Rule 2 later
        if _is_relative(node):
            continue

        module = _parse_import_module(node)
        if module is None or not _is_ncatbot_import(module):
            continue

        if _in_type_checking(node, tc_ranges):
            continue

        parts = _split_ncatbot(module)
        if _has_private_segment(parts):
            continue

        imported_layer = parts[0] if parts else None
        depth = _depth(parts)

        stmt = ast.get_source_segment(source, node)
        if stmt is None:
            # Fallback: reconstruct
            names = ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "") for a in node.names
            )
            stmt = f"from {module} import {names}"
        # Truncate very long statements
        if len(stmt) > 120:
            stmt = stmt[:117] + "..."

        # ----- Rule 2: same-layer must use relative import -----
        if src_layer and imported_layer == src_layer:
            violations.append(
                Violation(
                    rel,
                    node.lineno,
                    stmt,
                    "Rule2",
                    f"Same-layer ({src_layer}) import must use relative import",
                )
            )
            continue  # Don't double-report on Rule 1

        # ----- Rule 1: cross-layer max 2 levels -----
        if depth == 1:
            # ``from ncatbot.<layer> import ...`` — always OK
            continue

        if depth == 2:
            layer, sub = parts[0], parts[1]
            if _is_platform_2level_ok(layer, sub):
                continue
            # Non-whitelisted 2-level
            violations.append(
                Violation(
                    rel,
                    node.lineno,
                    stmt,
                    "Rule1",
                    f"2-level import from non-platform layer '{layer}' "
                    f"(only 1-level allowed, or use a whitelisted platform sub-module)",
                )
            )
            continue

        # depth >= 3
        # CLI exception: function-level imports in CLI exempt files
        if rel in CLI_EXEMPT_FILES and _is_in_function(node, tree):
            continue

        violations.append(
            Violation(
                rel,
                node.lineno,
                stmt,
                "Rule1",
                f"Import depth {depth} exceeds max 2 (from ncatbot.{'.'.join(parts[:2])}...)",
            )
        )

    # ----- Rule 2 extra: check that same-layer uses relative -----
    # Already covered above via absolute import check.
    # Additionally check ``import ncatbot.<same_layer>`` style:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name and alias.name.startswith("ncatbot."):
                    if _in_type_checking(node, tc_ranges):
                        continue
                    imp_parts = alias.name.split(".")[1:]
                    if imp_parts and imp_parts[0] == src_layer:
                        stmt_str = f"import {alias.name}"
                        violations.append(
                            Violation(
                                rel,
                                node.lineno,
                                stmt_str,
                                "Rule2",
                                f"Same-layer ({src_layer}) import must use relative import",
                            )
                        )

    return violations


# ---------------------------------------------------------------------------
# Regex-based checker for .md code blocks
# ---------------------------------------------------------------------------

_CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)
_IMPORT_RE = re.compile(
    r"^(?:from\s+ncatbot\.\S+\s+import\s+.+|import\s+ncatbot\.\S+)", re.MULTILINE
)
_COUNTER_EXAMPLE_RE = re.compile(
    r"#\s*❌|#\s*错误|#\s*WRONG|#\s*禁止|#\s*FORBIDDEN", re.IGNORECASE
)


def check_md_file(filepath: Path) -> list[Violation]:
    violations: list[Violation] = []
    rel = _posix(filepath)

    try:
        content = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return violations

    for block_match in _CODE_BLOCK_RE.finditer(content):
        block = block_match.group(1)
        block_start_line = content[: block_match.start()].count("\n") + 2

        block_lines = block.split("\n")

        for imp_match in _IMPORT_RE.finditer(block):
            line_in_block = block[: imp_match.start()].count("\n")
            abs_line = block_start_line + line_in_block
            stmt = imp_match.group(0).strip()

            # Skip counter-examples: check the current line AND preceding
            # lines within the block for ❌ markers. If a ❌ appears closer
            # than the most recent ✅, this import is a deliberate bad example.
            line_end = block.find("\n", imp_match.start())
            if line_end == -1:
                line_end = len(block)
            full_line = block[imp_match.start() : line_end]
            if _COUNTER_EXAMPLE_RE.search(full_line):
                continue
            # Check preceding lines (up to 10) for ❌ context
            _skip = False
            for lookback in range(1, min(line_in_block + 1, 11)):
                prev = block_lines[line_in_block - lookback]
                if re.search(r"#\s*✅|#\s*正确|#\s*CORRECT", prev, re.IGNORECASE):
                    break  # hit a ✅ marker first, import is OK
                if _COUNTER_EXAMPLE_RE.search(prev):
                    _skip = True
                    break
            if _skip:
                continue

            # Parse the import
            m = re.match(r"from\s+(ncatbot\.\S+)\s+import", stmt)
            if not m:
                m2 = re.match(r"import\s+(ncatbot\.\S+)", stmt)
                if not m2:
                    continue
                module = m2.group(1)
            else:
                module = m.group(1)

            parts = module.split(".")[1:]
            if _has_private_segment(parts):
                continue

            depth = len(parts)
            if depth <= 1:
                continue

            if depth == 2:
                layer, sub = parts[0], parts[1]
                if _is_platform_2level_ok(layer, sub):
                    continue
                violations.append(
                    Violation(
                        rel,
                        abs_line,
                        stmt,
                        "Rule1",
                        f"2-level import from non-platform layer '{layer}' in docs/skills",
                    )
                )
                continue

            # depth >= 3
            violations.append(
                Violation(
                    rel,
                    abs_line,
                    stmt,
                    "Rule1",
                    f"Import depth {depth} exceeds max 2 in docs/skills",
                )
            )

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    stat_only = "--stat" in sys.argv

    all_violations: list[Violation] = []

    # Scan .py files
    for dirname in SCAN_DIRS_PY:
        scan_dir = _root / dirname
        if not scan_dir.exists():
            continue
        for py_file in sorted(scan_dir.rglob("*.py")):
            all_violations.extend(check_py_file(py_file))

    # Scan .md files
    for dirname in SCAN_DIRS_MD:
        scan_dir = _root / dirname
        if not scan_dir.exists():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
            all_violations.extend(check_md_file(md_file))

    # Report
    if not all_violations:
        print("✅  All imports comply with conventions.")
        return 0

    rule1 = [v for v in all_violations if v.rule == "Rule1"]
    rule2 = [v for v in all_violations if v.rule == "Rule2"]

    print(
        f"❌  Found {len(all_violations)} import violations "
        f"(Rule1: {len(rule1)}, Rule2: {len(rule2)})\n"
    )

    if not stat_only:
        if rule1:
            print("── Rule 1: Cross-layer depth violations ──")
            for v in rule1:
                print(v)
            print()

        if rule2:
            print("── Rule 2: Same-layer absolute import violations ──")
            for v in rule2:
                print(v)
            print()

    # Summary by file
    by_file: dict[str, int] = {}
    for v in all_violations:
        by_file[v.file] = by_file.get(v.file, 0) + 1

    print("── Summary by file ──")
    for f in sorted(by_file, key=lambda x: -by_file[x]):
        print(f"  {by_file[f]:3d}  {f}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
