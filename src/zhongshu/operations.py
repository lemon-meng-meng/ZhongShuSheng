"""核心文件操作工具模块。

所有对"系统目录"（非 home 主目录）的写操作都通过 pkexec 提权执行；
对 home 主目录内的操作则用普通权限直接执行，避免无谓的密码询问。
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import List, Optional, Tuple

try:
    import magic  # python3-magic / libmagic
    _HAS_MAGIC = True
except Exception:  # pragma: no cover - magic 为可选
    _HAS_MAGIC = False

from .i18n import gettext as _


def home_dir() -> str:
    """返回当前用户的 home 主目录绝对路径（带末尾 /）。"""
    return os.path.expanduser("~").rstrip("/") + "/"


def is_system_path(path: str) -> bool:
    """判断路径是否位于 home 主目录之外（即需要提权）。"""
    if not path:
        return False
    abs_path = os.path.abspath(os.path.expanduser(path))
    home = home_dir()
    return not (abs_path + "/").startswith(home)


def is_executable_binary(path: str) -> Tuple[bool, str]:
    """判断文件是否为可执行的二进制文件。

    优先使用 libmagic，不可用则退化为 'file' 命令 / 后缀判断。
    返回 (是否可执行, 描述)。
    """
    if not os.path.isfile(path):
        return False, _("目标不是普通文件")

    desc = ""
    if _HAS_MAGIC:
        try:
            desc = magic.from_file(path)
        except Exception:
            desc = ""
    if not desc:
        try:
            desc = subprocess.check_output(
                ["file", "-b", path], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            desc = ""

    low = desc.lower()
    if "elf" in low or "executable" in low or "shared object" in low:
        return True, desc
    # shell/xml 等脚本也允许授予运行权限
    if any(low.startswith(p) for p in ("ascii text", "text", "script", "unicode")):
        return False, desc + _("（脚本类文件，可授予运行权限）")
    return False, desc


def needs_auth_for_target(path: str) -> bool:
    """目标路径是否位于系统目录（用于判断是否需提权）。"""
    return is_system_path(path)


def build_command(action: str, **kwargs) -> List[str]:
    """根据动作类型构造命令列表（不含 pkexec 前缀）。"""
    action = action.lower()

    if action == "chmod_x":
        return ["chmod", "+x", kwargs["path"]]

    if action == "move":
        src = kwargs["path"]
        dest_dir = kwargs["dest"]
        dest_full = os.path.join(dest_dir, os.path.basename(src.rstrip("/")))
        return ["mv", "-f", "--", src, dest_full]

    if action == "rm":
        return ["rm", "-rf", "--", kwargs["path"]]

    if action == "mkdir":
        return ["mkdir", "-p", "--", kwargs["path"]]

    if action == "rename":
        return ["mv", "--", kwargs["path"], kwargs["new_path"]]

    raise ValueError(_("未知操作: {action}").format(action=action))


def wrap_with_pkexec(cmd: List[str]) -> List[str]:
    """如果命令的目标涉及系统目录则前置 pkexec。"""
    return ["pkexec"] + cmd


def run_command(cmd: List[str], use_auth: bool) -> Tuple[bool, str]:
    """同步执行命令。返回 (是否成功, 输出/错误信息)。"""
    final_cmd = wrap_with_pkexec(cmd) if use_auth else cmd
    try:
        proc = subprocess.run(
            final_cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        return False, _("命令不可用: {error}").format(error=e)
    if proc.returncode == 0:
        return True, proc.stdout.strip()
    return False, (proc.stderr.strip() or proc.stdout.strip() or _("操作失败"))


def join_path(parent: str, name: str) -> str:
    """拼接路径并去除冗余分隔符。"""
    return os.path.normpath(os.path.join(parent, name))


def validate_path(path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """校验路径合法性与存在性。"""
    if not path or not path.strip():
        return False, _("路径不能为空")
    path = os.path.abspath(os.path.expanduser(path))
    if path == "/":
        return False, _("不能对根目录执行此操作")
    if must_exist and not os.path.exists(path):
        return False, _("路径不存在: ") + path
    return True, path


def safe_is_dir(path: str) -> bool:
    return os.path.isdir(path) if os.path.exists(path) else False
