"""
插件 E2E 人工验收测试

逐个加载/卸载 examples/ 中的示例插件，由人类测试者判断 (Y/N/SKIP)。
每个插件加载后显示功能说明与可用命令，供测试者在群/私聊中手动验证。

用法:
    # 需要先配置 config.yaml 中的 napcat 连接信息
    # 设置环境变量指定测试目标:
    #   NAPCAT_TEST_GROUP  测试群号 (必填)

    python tests/e2e/plugin/run.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from ncatbot.app import BotClient
from ncatbot.utils import ncatbot_config


# ── 插件功能描述注册 ──────────────────────────────────────────

# 每个 example 的可测试功能描述 (key = manifest name)
PLUGIN_TEST_INFO: dict[str, dict] = {
    "hello_world": {
        "description": "最小可运行插件 — 回复 hello",
        "test_instructions": [
            "群里发送「hello」→ 应收到回复",
            "私聊发送「hello」→ 应收到私聊回复",
        ],
    },
    "event_handling": {
        "description": "事件处理三模式 — 装饰器、事件流、wait_event",
        "test_instructions": [
            "群里发送「ping」→ 应回复「pong」",
            "群里发送「状态」→ 应回复插件运行状态信息",
            "群里发送「确认测试」→ 应提示 15 秒内回复「确认」",
            "  └ 回复「确认」→ 应显示「操作已确认」",
            "  └ 超时不回复 → 应显示「操作超时已取消」",
        ],
    },
    "message_types": {
        "description": "消息构造与解析 — MessageArray、图文混排、合并转发",
        "test_instructions": [
            "群里发送「图文」→ 应收到图文混排消息",
            "群里发送「at我」→ 应收到 @你 的消息",
            "群里发送「转发」→ 应收到合并转发消息",
            "群里发送一张图片 → 应回复图片信息 (URL/尺寸等)",
        ],
    },
    "config_and_data": {
        "description": "配置与数据持久化 — ConfigMixin + DataMixin",
        "test_instructions": [
            "群里发送「查看配置」→ 应显示当前配置项",
            "群里发送「统计」→ 应显示消息计数和活跃用户",
            "群里发送「设置前缀 !」→ 应提示前缀已修改",
            "群里发送「重置统计」→ 应提示统计已清空",
        ],
    },
    "bot_api": {
        "description": "Bot API 使用大全 — 消息发送、群管理、信息查询",
        "test_instructions": [
            "群里发送「查群列表」→ 应返回 Bot 加入的群列表",
            "群里发送「查登录信息」→ 应返回 Bot 登录信息",
            "群里发送「查成员 @某人」→ 应返回该成员信息",
            "群里发送「发图片」→ 应发送一张示例图片",
            "群里发送「戳我」→ Bot 应戳你一下",
        ],
    },
    "hook_and_filter": {
        "description": "Hook 系统与过滤器 — 关键词屏蔽、执行日志、异常捕获",
        "test_instructions": [
            "群里发送「回声 你好」→ 应回复「你好」",
            "群里发送「除零」→ 应触发异常并自动回复错误提示",
            "私聊发送任意消息 → 应验证 private_only 过滤器",
        ],
    },
    "rbac": {
        "description": "权限管理系统 — RBAC 角色、权限、用户绑定",
        "test_instructions": [
            "群里发送「查权限」→ 应显示当前权限",
            "群里发送「权限信息」→ 应显示 RBAC 系统配置",
            "群里发送「管理命令」→ 应因无权限被拒绝",
            "群里发送「授权 @自己」→ 应授予 admin 角色",
            "再次发送「管理命令」→ 应成功执行",
        ],
    },
    "scheduled_tasks": {
        "description": "定时任务 — 多种时间格式、条件执行、任务管理",
        "test_instructions": [
            "群里发送「任务列表」→ 应显示活跃定时任务",
            "群里发送「启动心跳」→ 应启动心跳任务 (观察日志)",
            "群里发送「停止心跳」→ 应停止心跳任务",
            "群里发送「添加提醒 10」→ 应在 10 秒后收到提醒",
        ],
    },
    "notice_and_request": {
        "description": "通知与请求事件 — 入群欢迎、戳一戳、好友请求",
        "test_instructions": [
            "在群里戳 Bot → Bot 应回戳 (或回复戳一戳消息)",
            "(如有条件) 邀请新成员入群 → 应自动发送欢迎消息",
            "观察日志输出是否记录通知事件",
        ],
    },
    "multi_step_dialog": {
        "description": "多步对话 — 连续交互、超时处理、取消退出",
        "test_instructions": [
            "群里发送「注册」→ 应开始多步对话",
            "  └ 输入名字 → 应提示输入年龄",
            "  └ 输入年龄 → 应提示确认",
            "  └ 输入「确认」→ 应保存信息",
            "重新发送「注册」后输入「取消」→ 应中止对话",
        ],
    },
    "group_manager": {
        "description": "群管理机器人 — 踢人/禁言/欢迎/RBAC",
        "test_instructions": [
            "群里发送「授管理 @自己」→ 应授予管理权限",
            "群里发送「禁言 @某人 10」→ 应禁言 10 秒 (需 Bot 是管理员)",
            "群里发送「解禁 @某人」→ 应解除禁言",
            "群里发送「设置欢迎语 欢迎新人!」→ 应修改欢迎消息",
            "⚠ 踢人操作请谨慎测试",
        ],
    },
    "qa_bot": {
        "description": "问答机器人 — 多步对话添加 QA、关键词匹配",
        "test_instructions": [
            "群里发送「添加问答」→ 应进入多步对话",
            "  └ 输入问题「天气」→ 应提示输入答案",
            "  └ 输入答案「今天晴天」→ 应保存问答对",
            "群里发送「天气」→ 应自动回复「今天晴天」",
            "群里发送「问答列表」→ 应列出所有问答对",
            "群里发送「删除问答 天气」→ 应删除",
        ],
    },
    "scheduled_reporter": {
        "description": "定时报告与统计 — 消息活跃度、合并转发报告",
        "test_instructions": [
            "群里发送「开启统计」→ 应开始统计消息",
            "发几条消息后发送「统计报告」→ 应显示活跃度统计",
            "群里发送「今日热词」→ 应显示高频关键词",
            "群里发送「关闭统计」→ 应停止统计",
        ],
    },
    "external_api": {
        "description": "外部 API 集成 — HTTP 请求、配置管理",
        "test_instructions": [
            "群里发送「每日一言」→ 应返回一句随机名言",
            "群里发送「api状态」→ 应显示 API 配置信息",
            "群里发送「随机图片」→ 应发送一张示例图片",
        ],
    },
    "full_featured_bot": {
        "description": "全功能群助手 — 综合演示所有框架特性",
        "test_instructions": [
            "群里发送「帮助」→ 应列出所有可用命令",
            "群里发送「签到」→ 应获取积分 (1-20)",
            "群里发送「积分」→ 应显示自己的积分",
            "群里发送「排行榜」→ 应显示积分排行",
            "群里发送「添加关键词 Q=A」→ 应添加自动回复",
            "群里发送「关键词列表」→ 应列出关键词",
            "群里发送「授权 @自己」→ 应授予管理权限",
        ],
    },
}


# ── 测试结果 ──────────────────────────────────────────────────


@dataclass
class PluginTestResult:
    name: str
    verdict: str  # "PASS", "FAIL", "SKIP"
    elapsed: float = 0.0
    note: str = ""


@dataclass
class PluginTestReport:
    results: list[PluginTestResult] = field(default_factory=list)

    def add(self, result: PluginTestResult) -> None:
        self.results.append(result)

    def summary(self) -> None:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.verdict == "PASS")
        failed = sum(1 for r in self.results if r.verdict == "FAIL")
        skipped = sum(1 for r in self.results if r.verdict == "SKIP")

        print(f"\n{'=' * 60}")
        print(f"  总计: {total}  通过: {passed}  失败: {failed}  跳过: {skipped}")

        if failed:
            print("\n  失败项:")
            for r in self.results:
                if r.verdict == "FAIL":
                    note = f" ({r.note})" if r.note else ""
                    print(f"    - {r.name}{note}")
        if skipped:
            print("\n  跳过项:")
            for r in self.results:
                if r.verdict == "SKIP":
                    note = f" ({r.note})" if r.note else ""
                    print(f"    - {r.name}{note}")
        print(f"{'=' * 60}")


# ── 人工交互 ──────────────────────────────────────────────────


def ask_verdict(plugin_name: str) -> tuple[str, str]:
    """向测试者请求判定结果。

    Returns:
        (verdict, note)
    """
    print()
    while True:
        answer = (
            input(
                f"  [{plugin_name}] 测试结果? (Y=通过 / N=失败 / S=跳过 / Q=退出全部): "
            )
            .strip()
            .upper()
        )
        if answer in ("Y", "YES"):
            return "PASS", ""
        if answer in ("N", "NO"):
            note = input("    失败原因 (可选，回车跳过): ").strip()
            return "FAIL", note
        if answer in ("S", "SKIP"):
            return "SKIP", ""
        if answer in ("Q", "QUIT"):
            return "QUIT", ""
        print("    请输入 Y / N / S / Q")


def show_plugin_info(
    name: str, description: str, folder: str, instructions: list[str]
) -> None:
    """展示插件信息和测试指引。"""
    print(f"\n{'─' * 60}")
    print(f"  插件: {name}  ({folder})")
    print(f"  描述: {description}")
    print(f"{'─' * 60}")
    print("  可测试功能:")
    for instruction in instructions:
        print(f"    • {instruction}")
    print()
    print("  ▶ 插件已加载，请在群/私聊中进行测试。")
    print("    测试完成后回到此终端输入结果。")


# ── 主流程 ──────────────────────────────────────────────────


def discover_examples(examples_dir: Path) -> list[tuple[str, Path]]:
    """扫描 examples/ 目录，返回 (folder_name, path) 列表，按目录名排序。"""
    results = []
    for entry in sorted(examples_dir.iterdir()):
        if entry.is_dir() and (entry / "manifest.toml").exists():
            results.append((entry.name, entry))
    return results


async def main() -> int:
    group_id_str = os.environ.get("NAPCAT_TEST_GROUP", "")
    if not group_id_str:
        print("错误: 请设置环境变量 NAPCAT_TEST_GROUP")
        print("  例: $env:NAPCAT_TEST_GROUP='123456'")
        return 1

    # 定位 examples 目录
    project_root = Path(__file__).resolve().parents[3]
    examples_dir = project_root / "examples"
    if not examples_dir.is_dir():
        print(f"错误: examples 目录不存在: {examples_dir}")
        return 1

    examples = discover_examples(examples_dir)
    if not examples:
        print("错误: examples 目录中未找到带 manifest.toml 的插件")
        return 1

    # 强制 skip_setup
    ncatbot_config.update_napcat(skip_setup=True)

    print("插件 E2E 人工验收测试")
    print(f"  WS:     {ncatbot_config.napcat.ws_uri}")
    print(f"  群号:   {group_id_str}")
    print(f"  插件数: {len(examples)}")
    print(f"{'=' * 60}")

    # 列出所有待测试插件
    print("\n  待测试插件:")
    for i, (folder_name, _) in enumerate(examples, 1):
        info = PLUGIN_TEST_INFO.get(
            folder_name.split("_", 1)[1] if "_" in folder_name else folder_name, {}
        )
        desc = info.get("description", "(无描述)")
        print(f"    {i:2d}. {folder_name} — {desc}")

    print(f"\n{'=' * 60}")
    print("  正在启动 Bot...")

    bot = BotClient()
    report = PluginTestReport()

    try:
        await bot.run_async()
        loader = bot.plugin_loader

        for folder_name, example_path in examples:
            # 从 folder_name 推导 manifest name
            # examples 用编号前缀如 "01_hello_world"，manifest name 去掉编号
            parts = folder_name.split("_", 1)
            manifest_name_guess = parts[1] if len(parts) > 1 else folder_name
            info = PLUGIN_TEST_INFO.get(manifest_name_guess, {})
            description = info.get("description", "(无描述)")
            instructions = info.get("test_instructions", ["(无测试说明，请自行探索)"])

            # 索引并加载插件
            print(f"\n  ⏳ 正在加载: {folder_name}...")
            loader._indexer.index_plugin(example_path)
            loader._importer.add_plugin_root(example_path.parent)

            # 获取索引后的实际 manifest name
            manifest = loader._indexer.get_by_folder(example_path.name)
            if manifest is None:
                print(f"  ⚠ 索引失败: {folder_name}，跳过")
                report.add(
                    PluginTestResult(name=folder_name, verdict="SKIP", note="索引失败")
                )
                continue

            plugin_name = manifest.name
            t0 = time.monotonic()

            plugin = await loader.load_plugin(plugin_name)
            if plugin is None:
                print(f"  ⚠ 加载失败: {plugin_name}，跳过")
                report.add(
                    PluginTestResult(name=plugin_name, verdict="SKIP", note="加载失败")
                )
                continue

            print(f"  ✓ 已加载: {plugin_name}")

            # 展示测试信息
            show_plugin_info(plugin_name, description, folder_name, instructions)

            # 等待人工判定
            verdict, note = ask_verdict(plugin_name)

            elapsed = time.monotonic() - t0

            if verdict == "QUIT":
                print("\n  用户中止测试。")
                # 卸载当前插件
                await loader.unload_plugin(plugin_name)
                report.add(
                    PluginTestResult(
                        name=plugin_name,
                        verdict="SKIP",
                        elapsed=elapsed,
                        note="用户中止",
                    )
                )
                break

            report.add(
                PluginTestResult(
                    name=plugin_name,
                    verdict=verdict,
                    elapsed=elapsed,
                    note=note,
                )
            )

            mark = {"PASS": "✓", "FAIL": "✗", "SKIP": "○"}[verdict]
            print(f"  [{mark}] {plugin_name}: {verdict}")

            # 卸载插件
            print(f"  ⏳ 正在卸载: {plugin_name}...")
            await loader.unload_plugin(plugin_name)
            print(f"  ✓ 已卸载: {plugin_name}")

    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await bot.shutdown()

    report.summary()
    failed = sum(1 for r in report.results if r.verdict == "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
