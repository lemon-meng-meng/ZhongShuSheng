"""Nautilus 右键菜单扩展：为「使用中书省操作」提供二级菜单。

兼容 Nautilus 3.x（python-nautilus 3.0）与 4.x（gnome-shell 42+）。
被 Nautilus 加载时，应位于以下任一位置之一：

  - /usr/share/nautilus-python/extensions/zhongshu_menu.py
  - ~/.local/share/nautilus-python/extensions/zhongshu_menu.py

需安装系统包：python3-nautilus
"""
from __future__ import annotations

import os
import subprocess
import urllib.parse

import gi
gi.require_version("Gtk", "4.0")
try:
    gi.require_version("Nautilus", "3.0")
    from gi.repository import Nautilus, GObject
except (ValueError, ImportError):
    # Nautilus 4.x（gir1.2-nautilus-4.0）命名空间不同
    try:
        gi.require_version("Nautilus", "4.0")
        from gi.repository import Nautilus, GObject
    except Exception:
        Nautilus = None
        GObject = None

# 应用启动器：必须存在 /usr/local/bin/zhongshu-app 或 /usr/bin/zhongshu-app
APP_LAUNCHER = os.environ.get("ZHONGSHU_LAUNCHER", "zhongshu-app")


def _uri_to_path(file_info) -> str:
    """将 Nautilus.FileInfo 转为本地路径。"""
    uri = file_info.get_uri()
    if file_info.get_uri_scheme() != "file":
        return ""
    parsed = urllib.parse.urlparse(uri)
    path = urllib.parse.unquote(parsed.path)
    return path


def _spawn(op: str, path: str = "", dest: str = "",
           parent: str = "", name: str = "") -> None:
    """非阻塞地启动中书省并进入指定操作界面。"""
    argv = [APP_LAUNCHER, f"--operation={op}"]
    if path:
        argv += ["--path", path]
    if dest:
        argv += ["--dest", dest]
    if parent:
        argv += ["--parent", parent]
    if name:
        argv += ["--name", name]
    # setsid 让子进程脱离 Nautilus，避免 Nautilus 退出时被杀
    subprocess.Popen(argv, start_new_session=True)


def _is_runnable_candidate(path: str) -> bool:
    """是否值得在右键菜单显示「授予运行权限」：普通文件即可。"""
    if not path:
        return False
    return os.path.isfile(path)


def _is_dir(path: str) -> bool:
    return os.path.isdir(path) if path else False


class ZhongshuMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    __gtype_name__ = "ZhongshuMenuProvider"

    def __init__(self):
        super().__init__()

    # 兼容 Nautilus 3.x 与 4.x：4.x 增加 get_background_items
    def get_file_items(self, *args):
        files = args[-1]
        if Nautilus is None or len(files) != 1:
            return []
        f = files[0]
        path = _uri_to_path(f)
        if not path:
            return []
        return self._build_menu(path, is_dir=_is_dir(path))

    def get_background_items(self, *args):
        # 在 Nautilus 4 中，背景菜单也需提供
        files = args[-1] if args else []
        if Nautilus is None or not files:
            # 一些 Nautilus 4 调用会传入一个表示当前目录的 FileInfo
            return []
        f = files[0]
        path = _uri_to_path(f)
        if not path:
            return []
        # 在空白处右键，仅提供「新建文件夹」和「新建文件」
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
            # 背景菜单：仅创建动作
            self._append(submenu, "新建文件夹",
                         lambda *_: self._new_folder(path))
            self._append(submenu, "新建文件",
                         lambda *_: self._new_file(path))
            return [top]

        # 对文件/文件夹的完整菜单
        self._append(submenu, "授予运行权限",
                     lambda *_: self._permission(path), enabled=not is_dir)
        self._append(submenu, "移动到…",
                     lambda *_: self._move(path))
        self._append(submenu, "删除",
                     lambda *_: self._delete(path))
        if is_dir:
            self._append(submenu, "新建文件夹（此处）",
                         lambda *_: self._new_folder(path))
            self._append(submenu, "新建文件（此处）",
                         lambda *_: self._new_file(path))
        self._append(submenu, "重命名",
                     lambda *_: self._rename(path))
        return [top]

    def _append(self, submenu, label, callback, enabled: bool = True):
        item = Nautilus.MenuItem(
            name=f"ZhongshuMenu::{label}", label=label)
        item.set_sensitive(enabled)
        item.connect("activate", callback)
        submenu.append_item(item)

    # --------- 操作分发 ---------
    def _permission(self, path: str) -> None:
        _spawn("permission", path=path)

    def _move(self, path: str) -> None:
        _spawn("move", path=path)

    def _delete(self, path: str) -> None:
        _spawn("delete", path=path)

    def _new_folder(self, parent: str) -> None:
        _spawn("new_folder", parent=parent)

    def _new_file(self, parent: str) -> None:
        _spawn("new_file", parent=parent)

    def _rename(self, path: str) -> None:
        _spawn("rename", path=path)
