"""Nautilus 右键菜单扩展：为「使用中书省操作」提供二级菜单。

兼容 Nautilus 3.x（python-nautilus 3.0）与 4.x（GNOME Files 42+）。
被 Nautilus 加载时应位于以下路径之一：

  - /usr/share/nautilus-python/extensions/zhongshu_menu.py        # deb 系统级安装
  - ~/.local/share/nautilus-python/extensions/zhongshu_menu.py    # AppImage 用户级安装

需安装系统包：python3-nautilus  以及  gir1.2-nautilus-4.0 (Nautilus 4) 或
gir1.2-nautilus-3.0 (Nautilus 3)。
"""
from __future__ import annotations

import os
import subprocess
import urllib.parse

import gi

# Nautilus 命名空间优先 4.x，再退化 3.x；不要硬性依赖 Gtk（扩展本身不需要它）。
Nautilus = None
GObject = None
for _ns in ("4.0", "3.0"):
    try:
        gi.require_version("Nautilus", _ns)
        from gi.repository import Nautilus, GObject  # type: ignore
        break
    except (ValueError, ImportError):
        continue

# 应用启动器定位策略：
#   1) ZHONGSHU_LAUNCHER 环境变量（由 AppImage 的 AppRun / 启动器设置）
#   2) 配置文件 ~/.config/zhongshu/launcher.path（部署脚本写入的真实路径）
#   3) 用户级部署 ~/.local/bin/zhongshu-app
#   4) deb 安装的 /usr/bin/zhongshu-app
#   5) 退化：直接 'zhongshu-app'，交给 PATH
_DEFAULT_CANDIDATES = [
    os.path.expanduser("~/.local/bin/zhongshu-app"),
    "/usr/local/bin/zhongshu-app",
    "/usr/bin/zhongshu-app",
]


def _resolve_launcher() -> str:
    env_l = os.environ.get("ZHONGSHU_LAUNCHER", "").strip()
    if env_l and os.path.exists(env_l):
        return env_l
    # 优先用户配置（AppImage 用户安装时写入）
    user_cfg = os.path.expanduser("~/.config/zhongshu/launcher.path")
    for cfg in (user_cfg, "/etc/zhongshu/launcher.path"):
        try:
            with open(cfg, "r", encoding="utf-8") as fh:
                p = fh.read().strip()
            if p and os.path.exists(p):
                return p
        except OSError:
            pass
    for c in _DEFAULT_CANDIDATES:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    return "zhongshu-app"


def _uri_to_path(file_info) -> str:
    """将 Nautilus.FileInfo 转为本地路径；非本地 file:// 资源返回空串。"""
    if file_info is None:
        return ""
    try:
        uri = file_info.get_uri()
    except Exception:
        return ""
    try:
        if file_info.get_uri_scheme() != "file":
            return ""
    except Exception:
        pass
    parsed = urllib.parse.urlparse(uri)
    return urllib.parse.unquote(parsed.path)


def _spawn(op: str, path: str = "", dest: str = "",
           parent: str = "", name: str = "") -> None:
    """非阻塞地启动中书省并进入指定操作界面。"""
    argv = [_resolve_launcher(), f"--operation={op}"]
    if path:
        argv += ["--path", path]
    if dest:
        argv += ["--dest", dest]
    if parent:
        argv += ["--parent", parent]
    if name:
        argv += ["--name", name]
    # setsid 让子进程脱离 Nautilus，避免 Nautilus 退出时被杀
    try:
        subprocess.Popen(argv, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        # 启动失败不至于让 Nautilus 崩溃；写入 stderr 供诊断。
        import sys
        sys.stderr.write(f"[zhongshu_menu] 启动失败: {e}; argv={argv}\n")


def _is_dir(path: str) -> bool:
    return bool(path) and os.path.isdir(path)


if Nautilus is not None and GObject is not None:

    class ZhongshuMenuProvider(GObject.GObject, Nautilus.MenuProvider):
        __gtype_name__ = "ZhongshuMenuProvider"

        def __init__(self):
            super().__init__()

        # Nautilus 3.x：get_file_items(self, files)
        # Nautilus 4.x：get_file_items(self, provider, files)
        def get_file_items(self, *args):
            files = args[-1]
            if not files or len(files) != 1:
                return []
            path = _uri_to_path(files[0])
            if not path:
                return []
            return self._build_menu(path, is_dir=_is_dir(path))

        # Nautilus 4.x 在空白处右键调用 get_background_items(provider, FileInfo_of_cwd)
        # Nautilus 3.x 调用 get_background_items(window) 或无参数
        def get_background_items(self, *args):
            files = args[-1] if args else None
            path = ""
            if files:
                # 4.x：files 是单个 FileInfo（当前目录）
                path = _uri_to_path(files if not isinstance(files, list) else files[0])
            if not path:
                # 3.x：拿不到 path，用 Nautilus 当前的 'current directory' 兜底
                try:
                    path = os.getcwd()
                except Exception:
                    path = ""
            if not path:
                return []
            return self._build_menu(path, is_dir=True, in_background=True)

        # --------- 菜单构造 ---------
        def _build_menu(self, path: str, is_dir: bool = False,
                        in_background: bool = False) -> list:
            top = Nautilus.MenuItem(
                name="ZhongshuMenu::top",
                label="使用中书省操作",
                tip="在非主目录下对文件进行特权操作",
            )
            submenu = Nautilus.Menu()
            top.set_submenu(submenu)

            if in_background:
                self._append(submenu, "新建文件夹",
                             lambda *_: _spawn("new_folder", parent=path))
                self._append(submenu, "新建文件",
                             lambda *_: _spawn("new_file", parent=path))
                return [top]

            self._append(submenu, "授予运行权限",
                         lambda *_: _spawn("permission", path=path),
                         enabled=not is_dir)
            self._append(submenu, "移动到…",
                         lambda *_: _spawn("move", path=path))
            self._append(submenu, "删除",
                         lambda *_: _spawn("delete", path=path))
            if is_dir:
                self._append(submenu, "新建文件夹（此处）",
                             lambda *_: _spawn("new_folder", parent=path))
                self._append(submenu, "新建文件（此处）",
                             lambda *_: _spawn("new_file", parent=path))
            self._append(submenu, "重命名",
                         lambda *_: _spawn("rename", path=path))
            return [top]

        def _append(self, submenu, label, callback, enabled: bool = True):
            item = Nautilus.MenuItem(
                name=f"ZhongshuMenu::{label}", label=label)
            if not enabled:
                try:
                    item.set_sensitive(False)
                except Exception:
                    pass
            item.connect("activate", callback)
            submenu.append_item(item)

else:
    # 类型缺失时定义占位类，避免 Nautilus 加载报错（极少数环境未装 gir）
    class ZhongshuMenuProvider:  # type: ignore
        pass
