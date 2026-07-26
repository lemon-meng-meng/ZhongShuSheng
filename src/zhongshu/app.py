"""中书省应用主入口（GTK4 + Libadwaita）。"""
from __future__ import annotations

import sys
from typing import Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk

from . import __app_id__, __app_name__, __version__
from .runner import parse_args, OperationRequest
from .window import MainWindow

CSS = b"""
.zhongshu-tile {
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: all 200ms ease;
}
.zhongshu-tile:hover {
    box-shadow: 0 6px 16px rgba(0,0,0,0.14);
}
.zhongshu-tile:active {
    transform: translateY(1px);
}
.warning-banner { background-color: #fa709a; }
"""


class ZhongshuApplication(Adw.Application):
    main_window: Optional[MainWindow] = None

    def __init__(self):
        super().__init__(application_id=__app_id__)

    def do_activate(self):
        if self.main_window is None:
            self.main_window = MainWindow(self)

        # 加载样式
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # 解析命令行参数：如果是右键菜单带参调用，直接进入二级界面
        argv = sys.argv[1:]
        req: Optional[OperationRequest] = None
        if argv:
            try:
                req = parse_args(argv)
            except SystemExit:
                # argparse 出错时终止
                self.quit()
                return

        if req is not None and req.operation:
            self.main_window._enter_operation(req)
        self.main_window.present()


def main():
    app = ZhongshuApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
