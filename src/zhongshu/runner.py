"""操作执行器与命令行参数解析。

此文件既被 GUI 主程序引用，也被 CLI 入口引用，统一封装：

1. 命令构造与提权决策。
2. pkexec 调用结果回调。
3. 命令行参数解析 —— 供 Nautilus 右键菜单调用：
   zhongshu-app --operation <op> [--path P] [--parent P] [--name N]
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Callable, List, Optional

from . import operations


@dataclass
class OperationRequest:
    """一次操作请求的完整信息。"""
    operation: str          # permission | move | delete | new_folder | rename | new_file
    path: str = ""          # 当前目标（文件/文件夹）路径
    dest: str = ""          # move 时的目标父目录
    new_name: str = ""      # new_folder / rename / new_file 时的新名称
    parent: str = ""        # new_folder / new_file 时的父目录

    @property
    def is_dir(self) -> Optional[bool]:
        if not self.path:
            return None
        return os.path.isdir(self.path) if os.path.exists(self.path) else None


def parse_args(argv: Optional[List[str]] = None) -> OperationRequest:
    """解析命令行参数。"""
    p = argparse.ArgumentParser(
        prog="zhongshu-app",
        description="中书省 - 系统目录文件管理工具",
    )
    p.add_argument("--operation", required=True,
                   choices=["permission", "move", "delete",
                            "new_folder", "new_file", "rename"])
    p.add_argument("--path", default="", help="目标文件或文件夹路径")
    p.add_argument("--dest", default="", help="移动操作的目标目录")
    p.add_argument("--parent", default="", help="新建操作的父目录")
    p.add_argument("--name", dest="new_name", default="", help="新建/重命名时的新名称")
    args = p.parse_args(argv)

    return OperationRequest(
        operation=args.operation,
        path=args.path,
        dest=args.dest,
        new_name=args.new_name,
        parent=args.parent,
    )


def build_command_for(req: OperationRequest) -> List[str]:
    """根据 OperationRequest 构造底层命令（不含 pkexec）。"""
    op = req.operation
    if op == "permission":
        return operations.build_command("chmod_x", path=req.path)
    if op == "move":
        return operations.build_command("move", path=req.path, dest=req.dest)
    if op == "delete":
        return operations.build_command("rm", path=req.path)
    if op == "new_folder":
        full = operations.join_path(req.parent or "/opt", req.new_name)
        return operations.build_command("mkdir", path=full)
    if op == "new_file":
        # 用空文件创建
        full = operations.join_path(req.parent or "/opt", req.new_name)
        return ["sh", "-c", f"umask 022; > {full!r}"]
    if op == "rename":
        new_path = operations.join_path(os.path.dirname(req.path), req.new_name)
        return operations.build_command("rename", path=req.path, new_path=new_path)
    raise ValueError(f"未知操作: {op}")


class OperationRunner:
    """封装操作执行与回调；GUI 通过此类异步执行命令。"""

    def __init__(self, on_done: Optional[Callable[[bool, str], None]] = None):
        self.on_done = on_done

    def run(self, req: OperationRequest) -> None:
        cmd = build_command_for(req)
        # 提权判定：源或目标任一在系统目录则提权
        targets = [req.path, req.dest, req.parent,
                   operations.join_path(req.parent, req.new_name) if req.new_name else ""]
        use_auth = any(operations.needs_auth_for_target(t) for t in targets if t)
        try:
            import gi  # noqa: F401
            gi.require_version("Gtk", "4.0")
            from gi.repository import Gio, GLib
            final_cmd = operations.wrap_with_pkexec(cmd) if use_auth else cmd
            proc = Gio.Subprocess.new(
                final_cmd,
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            )
            proc.wait_check_async(None, self._gio_callback)
        except Exception:
            # 无 GTK 上下文（CLI 模式）则同步执行
            ok, msg = operations.run_command(cmd, use_auth)
            if self.on_done:
                self.on_done(ok, msg)

    def _gio_callback(self, proc, result):
        from gi.repository import GLib
        try:
            proc.wait_check_finish(result)
            if self.on_done:
                self.on_done(True, "操作成功")
        except GLib.Error as e:
            if self.on_done:
                self.on_done(False, e.message or "操作失败")
