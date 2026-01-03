"""
测试报告生成器

支持 JSON 和 Markdown 格式。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .types import TestResult, TestStatus


class TestReporter:
    """测试报告生成器"""

    def __init__(self, results: List[TestResult]):
        self.results = results
        self.generated_at = datetime.now()

    def _get_stats(self) -> dict:
        """获取统计数据"""
        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.status == TestStatus.PASSED),
            "failed": sum(1 for r in self.results if r.status == TestStatus.FAILED),
            "skipped": sum(1 for r in self.results if r.status == TestStatus.SKIPPED),
            "error": sum(1 for r in self.results if r.status == TestStatus.ERROR),
        }

    def to_json(self) -> str:
        """生成 JSON 报告"""
        data = {
            "generated_at": self.generated_at.isoformat(),
            "stats": self._get_stats(),
            "results": [],
        }

        for result in self.results:
            item = {
                "name": result.test_case.name,
                "category": result.test_case.category,
                "api_endpoint": result.test_case.api_endpoint,
                "status": result.status.value,
                "duration": result.duration,
                "human_comment": result.human_comment,
                "error": result.error,
            }
            data["results"].append(item)

        return json.dumps(data, indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        """生成 Markdown 报告"""
        stats = self._get_stats()
        lines = [
            "# API 端到端测试报告",
            "",
            f"**生成时间**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 统计",
            "",
            "| 状态 | 数量 |",
            "|------|------|",
            f"| ✅ 通过 | {stats['passed']} |",
            f"| ❌ 失败 | {stats['failed']} |",
            f"| ⏭️ 跳过 | {stats['skipped']} |",
            f"| ⚠️ 错误 | {stats['error']} |",
            f"| **总计** | **{stats['total']}** |",
            "",
            "## 测试详情",
            "",
        ]

        # 按分类分组
        categories = {}
        for result in self.results:
            cat = result.test_case.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)

        for category, results in categories.items():
            lines.append(f"### {category.upper()}")
            lines.append("")
            lines.append("| 测试名称 | API | 状态 | 耗时 | 备注 |")
            lines.append("|----------|-----|------|------|------|")

            for result in results:
                status_emoji = {
                    TestStatus.PASSED: "✅",
                    TestStatus.FAILED: "❌",
                    TestStatus.SKIPPED: "⏭️",
                    TestStatus.ERROR: "⚠️",
                }.get(result.status, "❓")

                duration = f"{result.duration:.2f}s" if result.duration else "-"
                comment = result.human_comment or result.error or "-"
                if len(comment) > 50:
                    comment = comment[:47] + "..."

                lines.append(
                    f"| {result.test_case.name} | "
                    f"`{result.test_case.api_endpoint}` | "
                    f"{status_emoji} | {duration} | {comment} |"
                )

            lines.append("")

        # 失败详情
        failed = [
            r for r in self.results if r.status in [TestStatus.FAILED, TestStatus.ERROR]
        ]
        if failed:
            lines.extend(self._format_failures(failed))

        return "\n".join(lines)

    def _format_failures(self, failed_results: List[TestResult]) -> List[str]:
        """格式化失败详情"""
        lines = ["## 失败详情", ""]

        for result in failed_results:
            lines.append(f"### {result.test_case.name}")
            lines.append("")
            lines.append(f"**API**: `{result.test_case.api_endpoint}`")
            lines.append("")
            lines.append(f"**预期**: {result.test_case.expected}")
            lines.append("")

            if result.error:
                lines.extend(["**错误**:", "```", result.error, "```"])

            if result.human_comment:
                lines.append(f"**人工评语**: {result.human_comment}")

            lines.append("")

        return lines

    def save(self, path: str, format: str = "markdown") -> None:
        """
        保存报告到文件

        Args:
            path: 文件路径
            format: 格式 (json, markdown)
        """
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            content = self.to_json()
        else:
            content = self.to_markdown()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
