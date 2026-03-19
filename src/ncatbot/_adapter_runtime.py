import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Literal, TypedDict

from .adapters import BaseAdapter, InternalEventAdapter
from .events import (
    AdapterAdded,
    AdapterRestartScheduled,
    AdapterRunExited,
    AdapterRunFailed,
    AdapterRunStarting,
    FrameworkEvent,
)


class AdapterEventKwargs(TypedDict):
    adapter_name: str
    platform_name: str
    adapter_version: str


type DispatchEvent = Callable[[object, BaseAdapter], Awaitable[None]]
type EmitFrameworkEvent = Callable[[FrameworkEvent], None]
type RuntimePredicate = Callable[[], bool]


def adapter_event_kwargs(adapter: BaseAdapter) -> AdapterEventKwargs:
    return {
        "adapter_name": adapter.adapter_name,
        "platform_name": adapter.platform_name,
        "adapter_version": adapter.adapter_version,
    }


class AdapterRuntime:
    """Own adapter attachment, task supervision, and restart behavior."""

    def __init__(
        self,
        *,
        adapter_restart_delay: float,
        dispatch_event: DispatchEvent,
        emit_framework_event: EmitFrameworkEvent,
        is_running: RuntimePredicate,
        is_stop_requested: RuntimePredicate,
        logger: logging.Logger,
    ) -> None:
        self.adapters: list[BaseAdapter] = []
        self._adapter_tasks: dict[BaseAdapter, asyncio.Task[None]] = {}
        self._adapter_restart_delay = adapter_restart_delay
        self._dispatch_event = dispatch_event
        self._emit_framework_event = emit_framework_event
        self._is_running = is_running
        self._is_stop_requested = is_stop_requested
        self._logger = logger
        self._internal_adapter = InternalEventAdapter()
        self.attach(self._internal_adapter)

    @property
    def internal_adapter(self) -> InternalEventAdapter:
        return self._internal_adapter

    def is_internal_adapter(self, adapter: BaseAdapter) -> bool:
        return adapter is self._internal_adapter

    def attach(self, adapter: BaseAdapter) -> None:
        """Register an adapter instance without starting it yet."""
        if any(existing is adapter for existing in self.adapters):
            raise ValueError("同一个 adapter 实例不能重复添加")
        self.adapters.append(adapter)

    def prepare_runtime(self) -> None:
        self._adapter_tasks = {}

    def reset_runtime(self) -> None:
        self._adapter_tasks = {}

    def add_adapter(
        self,
        adapter: BaseAdapter,
        *,
        running: bool,
        loop: asyncio.AbstractEventLoop | None,
    ) -> None:
        """Attach an adapter and start it immediately when the app is already running."""
        self.attach(adapter)
        if not self.is_internal_adapter(adapter):
            self._emit_framework_event(AdapterAdded(**adapter_event_kwargs(adapter)))

        if running and loop is not None:
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                current_loop = None

            if current_loop is loop:
                self._spawn_adapter_task(adapter)
            else:
                loop.call_soon_threadsafe(self._spawn_adapter_task, adapter)

    def start_all(self) -> None:
        """Spawn runtime tasks for every currently attached adapter."""
        for adapter in self.adapters:
            self._spawn_adapter_task(adapter)

    async def cancel_tasks(self, *, include_internal: bool) -> None:
        """Cancel supervised adapter tasks, optionally keeping the internal adapter alive."""
        tasks = tuple(
            task
            for adapter, task in self._adapter_tasks.items()
            if include_internal or not self.is_internal_adapter(adapter)
        )
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _spawn_adapter_task(self, adapter: BaseAdapter) -> None:
        task = asyncio.create_task(self._run_adapter(adapter))
        self._adapter_tasks[adapter] = task
        task.add_done_callback(lambda _: self._adapter_tasks.pop(adapter, None))

    async def _run_adapter(self, adapter: BaseAdapter) -> None:
        """Run one adapter until it stops, fails, or is cancelled."""
        attempt = 0
        while True:
            attempt += 1
            if not self.is_internal_adapter(adapter):
                self._emit_framework_event(
                    AdapterRunStarting(
                        **adapter_event_kwargs(adapter),
                        attempt=attempt,
                    )
                )

            exit_reason: Literal["completed", "failed", "stopped"] = "completed"
            try:
                async with adapter:
                    async for event_obj in adapter:
                        await self._dispatch_event(event_obj, adapter)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                exit_reason = "failed"
                if not self.is_internal_adapter(adapter):
                    self._emit_framework_event(
                        AdapterRunFailed(
                            **adapter_event_kwargs(adapter),
                            attempt=attempt,
                            exception=exc,
                        )
                    )
                self._logger.exception("Adapter %s 发生错误", adapter.adapter_name)

            if self._is_stop_requested():
                exit_reason = "stopped"

            if not self.is_internal_adapter(adapter):
                self._emit_framework_event(
                    AdapterRunExited(
                        **adapter_event_kwargs(adapter),
                        attempt=attempt,
                        reason=exit_reason,
                    )
                )

            if not self._is_running() or self._is_stop_requested():
                return

            if not self.is_internal_adapter(adapter):
                self._emit_framework_event(
                    AdapterRestartScheduled(
                        **adapter_event_kwargs(adapter),
                        attempt=attempt,
                        delay=self._adapter_restart_delay,
                    )
                )
            self._logger.warning(
                "Adapter %s 已退出，%.2f 秒后重试",
                adapter.adapter_name,
                self._adapter_restart_delay,
            )
            await asyncio.sleep(self._adapter_restart_delay, result=None)
