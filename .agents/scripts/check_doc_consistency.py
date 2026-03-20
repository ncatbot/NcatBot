"""文档一致性自动检查脚本。

扫描 docs/、examples/、.agents/skills/ 下的 Markdown 文件，检查：
1. 断链：相对链接指向不存在的文件
2. 索引遗漏：目录中的 .md 文件未出现在父 README.md 索引中
3. 行数超限：文件超过 400 行（仅报告，不阻断）
4. 代码块规范：未标注语言的代码块
5. 结构检查：目录缺少 README.md
6. 示例完整：示例插件缺少 manifest.toml 或 main.py
7. Skill 完整：Skill 目录缺少 SKILL.md

用法：
    python .agents/scripts/check_doc_consistency.py [--json]

退出码：
    0 — 无阻断问题（LOC 超限只报告，不影响退出码）
    1 — 存在阻断问题（断链、索引遗漏、结构缺失等）
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Windows 默认 GBK 编码无法输出 emoji，强制 UTF-8
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def _find_root() -> Path:
    """向上查找含 pyproject.toml 的目录作为项目根。"""
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Cannot find project root (no pyproject.toml found)")


PROJECT_ROOT = _find_root()

SCAN_DIRS = [
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / ".agents" / "skills",
]

LOC_HARD_LIMIT = 400

# 匹配 Markdown 链接 [text](target) 和 [text](target#anchor)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# 匹配代码块开始 ``` 或 ```language
CODE_BLOCK_RE = re.compile(r"^```(\w*)$")

# 模板/占位链接模式，不计为真实断链
TEMPLATE_LINK_PATTERNS = [
    re.compile(r"\.\.\./"),  # 含 .../（占位路径）
    re.compile(r"前一篇"),  # 中文占位
    re.compile(r"/xxx"),  # 占位文件名
    re.compile(r"/XX/"),  # 占位目录名
]

# skills references 目录（允许使用项目根相对路径）
SKILLS_REF_DIR = PROJECT_ROOT / ".agents" / "skills"

# LOC 超限是警告，不阻断（不计入退出码）
LOC_WARN_ONLY = True

# 跳过的目录名
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".vuepress"}


def collect_md_files() -> list[Path]:
    """收集所有需要扫描的 Markdown 文件。"""
    files = []
    for d in SCAN_DIRS:
        if d.exists():
            for md in d.rglob("*.md"):
                if not any(part in SKIP_DIRS for part in md.relative_to(d).parts):
                    files.append(md)
    return sorted(files)


def _is_under_skills_refs(md: Path) -> bool:
    """判断文件是否在 .agents/skills/*/references/ 下。"""
    try:
        rel = md.relative_to(SKILLS_REF_DIR)
        parts = rel.parts
        return len(parts) >= 2 and parts[1] == "references"
    except ValueError:
        return False


def collect_dirs_needing_readme() -> list[Path]:
    """收集 docs/ 下含有 .md 文件的子目录（应有 README.md）。"""
    dirs = set()
    docs_dir = PROJECT_ROOT / "docs"
    if not docs_dir.exists():
        return []
    for md in docs_dir.rglob("*.md"):
        if any(part in SKIP_DIRS for part in md.relative_to(docs_dir).parts):
            continue
        parent = md.parent
        if parent != docs_dir:
            dirs.add(parent)
    return sorted(dirs)


def check_broken_links(md_files: list[Path]) -> list[dict]:
    """检查所有 Markdown 文件中的相对链接是否指向存在的文件。"""
    issues = []
    for md in md_files:
        content = md.read_text(encoding="utf-8", errors="replace")
        is_skill_ref = _is_under_skills_refs(md)
        for match in LINK_RE.finditer(content):
            target = match.group(2)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#")[0]
            if not target_path:
                continue
            if any(p.search(target_path) for p in TEMPLATE_LINK_PATTERNS):
                continue
            resolved = (md.parent / target_path).resolve()
            if not resolved.exists():
                if is_skill_ref:
                    root_resolved = (PROJECT_ROOT / target_path).resolve()
                    if root_resolved.exists():
                        continue
                line_no = content[: match.start()].count("\n") + 1
                issues.append(
                    {
                        "type": "broken_link",
                        "file": str(md.relative_to(PROJECT_ROOT)),
                        "line": line_no,
                        "link_text": match.group(1),
                        "target": target_path,
                    }
                )
    return issues


def check_index_coverage(md_files: list[Path]) -> list[dict]:
    """检查 README.md 索引是否覆盖了同目录下的所有 .md 文件。"""
    issues = []
    dir_files: dict[Path, list[Path]] = {}
    for md in md_files:
        dir_files.setdefault(md.parent, []).append(md)

    for directory, files in dir_files.items():
        readme = directory / "README.md"
        if not readme.exists():
            continue
        readme_content = readme.read_text(encoding="utf-8", errors="replace")
        sibling_mds = [
            f for f in files if f.name != "README.md" and f.parent == directory
        ]
        for sibling in sibling_mds:
            if sibling.name not in readme_content:
                issues.append(
                    {
                        "type": "missing_from_index",
                        "file": str(readme.relative_to(PROJECT_ROOT)),
                        "missing": sibling.name,
                        "detail": f"{sibling.name} 未在 {readme.relative_to(PROJECT_ROOT)} 中被引用",
                    }
                )
    return issues


def check_loc_limits(md_files: list[Path]) -> list[dict]:
    """检查文件行数是否超过硬限制（仅报告，不阻断）。"""
    issues = []
    exempt = {"architecture.md"}
    for md in md_files:
        if md.name in exempt:
            continue
        if md.name == "README.md" and md.parent == PROJECT_ROOT / "docs":
            continue
        line_count = len(md.read_text(encoding="utf-8", errors="replace").splitlines())
        if line_count > LOC_HARD_LIMIT:
            issues.append(
                {
                    "type": "loc_exceeded",
                    "warn_only": True,
                    "file": str(md.relative_to(PROJECT_ROOT)),
                    "lines": line_count,
                    "limit": LOC_HARD_LIMIT,
                }
            )
    return issues


def check_code_blocks(md_files: list[Path]) -> list[dict]:
    """检查代码块是否标注了语言（只检查开头行，不误报关闭行）。"""
    issues = []
    for md in md_files:
        content = md.read_text(encoding="utf-8", errors="replace")
        inside_block = False
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            match = CODE_BLOCK_RE.match(stripped)
            if not match:
                continue
            if not inside_block:
                # 开始行：检查是否有语言标识
                if not match.group(1):
                    issues.append(
                        {
                            "type": "unlabeled_code_block",
                            "file": str(md.relative_to(PROJECT_ROOT)),
                            "line": i,
                        }
                    )
                inside_block = True
            else:
                # 关闭行：不检查
                inside_block = False
    return issues


def check_missing_readme(dirs: list[Path]) -> list[dict]:
    """检查目录是否包含 README.md。"""
    issues = []
    for d in dirs:
        if not (d / "README.md").exists():
            issues.append(
                {
                    "type": "missing_readme",
                    "directory": str(d.relative_to(PROJECT_ROOT)),
                }
            )
    return issues


def check_example_structure() -> list[dict]:
    """检查示例插件的结构完整性（manifest.toml + main.py）。

    示例按平台子目录组织：common/qq/bilibili/github/cross_platform，
    每个平台目录下是编号的示例目录（如 01_hello_world/）。
    """
    issues = []
    examples_dir = PROJECT_ROOT / "docs" / "docs" / "examples"
    if not examples_dir.exists():
        return issues
    for platform_dir in sorted(examples_dir.iterdir()):
        if not platform_dir.is_dir() or platform_dir.name.startswith("."):
            continue
        for example_dir in sorted(platform_dir.iterdir()):
            if not example_dir.is_dir() or example_dir.name.startswith("."):
                continue
            for required in ("manifest.toml", "main.py"):
                if not (example_dir / required).exists():
                    issues.append(
                        {
                            "type": "example_missing_file",
                            "directory": str(example_dir.relative_to(PROJECT_ROOT)),
                            "missing": required,
                        }
                    )
    return issues


def check_skill_structure() -> list[dict]:
    """检查 skill 的结构完整性（SKILL.md 必须存在）。"""
    issues = []
    skills_dir = PROJECT_ROOT / ".agents" / "skills"
    if not skills_dir.exists():
        return issues
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not (child / "SKILL.md").exists():
            issues.append(
                {
                    "type": "skill_missing_file",
                    "directory": str(child.relative_to(PROJECT_ROOT)),
                    "missing": "SKILL.md",
                }
            )
    return issues


def main():
    parser = argparse.ArgumentParser(description="文档一致性检查")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    args = parser.parse_args()

    md_files = collect_md_files()
    dirs = collect_dirs_needing_readme()

    all_issues = []
    all_issues.extend(check_broken_links(md_files))
    all_issues.extend(check_index_coverage(md_files))
    all_issues.extend(check_loc_limits(md_files))
    all_issues.extend(check_code_blocks(md_files))
    all_issues.extend(check_missing_readme(dirs))
    all_issues.extend(check_example_structure())
    all_issues.extend(check_skill_structure())

    if args.json:
        print(json.dumps(all_issues, ensure_ascii=False, indent=2))
    else:
        if not all_issues:
            print("✅ 未发现问题")
            return

        by_type: dict[str, list] = {}
        for issue in all_issues:
            by_type.setdefault(issue["type"], []).append(issue)

        type_labels = {
            "broken_link": "🔗 断链",
            "missing_from_index": "📋 索引遗漏",
            "loc_exceeded": "📏 行数超限（仅报告）",
            "unlabeled_code_block": "📝 代码块未标注语言",
            "missing_readme": "📁 缺少 README.md",
            "example_missing_file": "📦 示例缺少文件",
            "skill_missing_file": "🛠️ Skill 缺少文件",
        }

        blocking_count = 0
        for issue_type, items in by_type.items():
            label = type_labels.get(issue_type, issue_type)
            print(f"\n{label} ({len(items)} 项)")
            print("-" * 50)
            for item in items:
                if issue_type == "broken_link":
                    print(
                        f"  {item['file']}:{item['line']}  [{item['link_text']}] → {item['target']}"
                    )
                elif issue_type == "missing_from_index":
                    print(f"  {item['detail']}")
                elif issue_type == "loc_exceeded":
                    print(
                        f"  {item['file']}: {item['lines']} 行 (限制 {item['limit']})"
                    )
                elif issue_type == "unlabeled_code_block":
                    print(f"  {item['file']}:{item['line']}")
                elif issue_type == "missing_readme":
                    print(f"  {item['directory']}/")
                elif issue_type in ("example_missing_file", "skill_missing_file"):
                    print(f"  {item['directory']}/  缺少 {item['missing']}")

            # LOC 超限不计入阻断
            if issue_type != "loc_exceeded":
                blocking_count += len(items)

        warn_only_count = len(by_type.get("loc_exceeded", []))
        if blocking_count == 0 and warn_only_count > 0:
            print(f"\n⚠️  {warn_only_count} 个行数超限（仅报告，不阻断）")
        elif blocking_count > 0:
            print(f"\n共发现 {blocking_count} 个阻断问题，{warn_only_count} 个警告")

    # 只有阻断问题才返回非零退出码
    blocking = [i for i in all_issues if i.get("type") != "loc_exceeded"]
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
