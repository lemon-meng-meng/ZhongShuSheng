"""中书省应用主入口（GTK4 + Libadwaita）。"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk

from . import __app_id__, __app_name__, __version__
from .runner import parse_args, OperationRequest
from .window import MainWindow
from .i18n import gettext as _

# 用于把 argv 通过环境变量绕过 GApplication 解析的自定义键。
# main() 会把 --operation 等参数抽出并写入此环境变量。
ARGV_ENV_KEY = "ZHONGSHU_ARGV"

# Nautilus 右键菜单带参调用使用以下前缀的所有参数；其它参数（GApplication 标准）
# 不属于此集合。
_OUR_OPTS = ("--operation", "--path", "--dest", "--parent", "--name", "--new-name")


def _split_our_args(argv):
    """从 argv 中抽出我们认识的参数；返回 (our_args, rest_args)。"""
    our, rest = [], []
    i = 0
    while i < len(argv):
        a = argv[i]
        key = a.split("=", 1)[0]
        if key in _OUR_OPTS:
            our.append(a)
            if "=" not in a and i + 1 < len(argv):
                our.append(argv[i + 1])
                i += 2
                continue
            i += 1
            continue
        rest.append(a)
        i += 1
    return our, rest


def _maybe_parse(argv) -> Optional[OperationRequest]:
    if not argv:
        return None
    try:
        return parse_args(argv)
    except SystemExit:
        return None


def _load_css(app_id: str) -> str:
    """加载 CSS 样式文件，支持源码运行、deb 安装、AppImage 多种场景。"""
    # 搜索 data/style.css 的可能位置
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        # 源码树：src/zhongshu/app.py -> ../../data/style.css
        os.path.normpath(os.path.join(here, "..", "..", "data", "style.css")),
        # deb 安装：/opt/zhongshu/data/style.css
        "/opt/zhongshu/data/style.css",
        # AppImage：usr/lib/zhongshu/src/zhongshu/app.py -> ../../../share/zhongshu/data/style.css
        os.path.normpath(os.path.join(here, "..", "..", "..", "..", "share", "zhongshu", "data", "style.css")),
        # APPDIR 环境变量
        (os.path.join(os.environ.get("APPDIR", ""), "usr", "share", "zhongshu", "data", "style.css")
         if os.environ.get("APPDIR") else ""),
    ]
    for css_path in candidates:
        if css_path and os.path.isfile(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                return f.read()
    # 兜底：内联备用样式（不含字体定义）
    return """
.zhongshu-tile { border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: box-shadow 200ms ease, transform 200ms ease; }
.zhongshu-tile:hover { box-shadow: 0 6px 16px rgba(0,0,0,0.14); transform: translateY(-1px); }
.zhongshu-tile:active { transform: translateY(1px); box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
.warning-banner { background-color: #fa709a; color: white; }
.dim-label { opacity: 0.7; }
"""


class ZhongshuApplication(Adw.Application):
    main_window: Optional[MainWindow] = None

    def __init__(self):
        # NON_UNIQUE 允许多实例（Nautilus 多次右键调用各自打开窗口）。
        super().__init__(application_id=__app_id__,
                         flags=Gio.ApplicationFlags.NON_UNIQUE)

    def do_activate(self):
        if self.main_window is None:
            self.main_window = MainWindow(self)

        # 加载样式
        css_content = _load_css(__app_id__)
        provider = Gtk.CssProvider()
        provider.load_from_data(css_content.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # 由 main() 抽出的自定义参数写入环境变量绕过 GApplication，
        # 这里取出来并进入对应操作界面。
        argv_env = os.environ.get(ARGV_ENV_KEY)
        argv = argv_env.split("\x1f") if argv_env else []
        req = _maybe_parse(argv)

        if req is not None and req.operation:
            self.main_window._enter_operation(req)
        self.main_window.present()


def main():
    # 拦截右键菜单部署子命令（无需 GTK/UI）
    argv = sys.argv[1:]
    if argv and argv[0] in ("--install-context-menu", "--uninstall-context-menu",
                            "install-context-menu", "uninstall-context-menu"):
        return _handle_context_menu_subcommand(argv)

    # 抽出我们的自定义参数，避免被 GApplication 拦截报「未知选项」。
    # 我们用 US(\x1f) 分隔参数与值，回避对含空格/特殊字符路径的引号问题
    # （{\x1f} 是 ASCII Unit Separator，环境变量值允许）。
    our_args, _rest = _split_our_args(argv)
    if our_args:
        os.environ[ARGV_ENV_KEY] = "\x1f".join(our_args)
    elif ARGV_ENV_KEY in os.environ:
        # 之前可能存有环境变量（很少情况），清掉以免误进二级界面
        del os.environ[ARGV_ENV_KEY]

    # GApplication 接收 argv；保留 GApplication-理解的 argv[0] + 空参数
    # （我们已把 --operation 等抽走，剩下的留给 GApplication 解析；通常为空）
    app = ZhongshuApplication()
    # 让 GApplication 看到的 argv 只含程序名 + 非自定义参数，
    # 这样它不会因「未知选项 --operation」而退出。
    app_argv = [sys.argv[0]] + list(_rest)
    return app.run(app_argv)


def _handle_context_menu_subcommand(argv) -> int:
    """处理 --install-context-menu / --uninstall-context-menu 子命令。

    AppImage 模式下，脚本由 AppImage 内置（usr/share/zhongshu/scripts/）；
    源码树运行时，脚本就在源码树内；deb 安装后脚本在 /opt/zhongshu/scripts/。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        # AppImage 内置：app.py 在 usr/lib/zhongshu/src/zhongshu/app.py
        # scripts 在 usr/share/zhongshu/scripts/
        os.path.normpath(os.path.join(here, "..", "..", "..", "..",
                                       "share", "zhongshu", "scripts",
                                       "install-context-menu.sh")),
        # APPDIR 环境变量（AppRun 会 export）
        (os.path.join(os.environ.get("APPDIR", ""),
                      "usr/share/zhongshu/scripts/install-context-menu.sh")
         if os.environ.get("APPDIR") else ""),
        # deb 包安装
        "/opt/zhongshu/scripts/install-context-menu.sh",
        # 源码树
        os.path.normpath(os.path.join(here, "..", "..", "scripts",
                                       "install-context-menu.sh")),
    ]
    script = next((p for p in candidates if p and os.path.isfile(p)), None)
    if script is None:
        sys.stderr.write(
            _("未找到右键菜单部署脚本 install-context-menu.sh\n")
            + _("请从源码树运行，或安装 zhongshu.deb；AppImage 用户也可以手动运行\n")
            + _("源码树内的 scripts/install-context-menu.sh --appimage <AppImage绝对路径>。\n")
        )
        return 1

    extra = []
    if argv[0] in ("--uninstall-context-menu", "uninstall-context-menu"):
        extra.append("--uninstall")

    # 把当前可执行（AppImage）的路径传给脚本
    appimage = (os.environ.get("APPIMAGE")
                or os.environ.get("ZHONGSHU_APPIMAGE")
                or os.environ.get("ZHONGSHU_LAUNCHER"))
    if not appimage and sys.argv and sys.argv[0]:
        a0 = sys.argv[0]
        if os.path.isfile(a0) and a0.endswith(".AppImage"):
            appimage = os.path.abspath(a0)
    if not appimage and sys.executable and sys.executable.endswith(".AppImage"):
        appimage = sys.executable
    if appimage and os.path.isfile(appimage):
        extra += ["--appimage", os.path.abspath(appimage)]

    cmd = ["/bin/bash", script] + extra
    try:
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except OSError as e:
        sys.stderr.write(_("运行部署脚本失败: {error}\n").format(error=e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
