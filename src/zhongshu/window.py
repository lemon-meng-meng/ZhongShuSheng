"""中书省主窗口（一级界面）。

展示五项功能的网格按钮，点击进入对应的二级操作界面。
"""
from __future__ import annotations

import os
from typing import Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from .operation_view import OperationView
from . import operations
from .i18n import _, get_available_languages, set_language, get_current_language, get_available_font_weights, get_font_weight, set_font_weight, apply_font_weight_css


OPERATION_LABELS = [
    ("permission", _("授予运行权限"), "system-run"),
    ("move", _("移动到"), "folder-move"),
    ("delete", _("删除"), "user-trash"),
    ("new_folder", _("新建文件夹"), "folder-new"),
    ("new_file", _("新建文件"), "document-new"),
    ("rename", _("重命名"), "edit-rename"),
]


class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ZhongshuMainWindow"

    def __init__(self, app, initial_request=None):
        super().__init__(application=app)
        self.set_title(_("中书省"))
        self.set_default_size(900, 600)

        # 主布局
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.root_box)

        self.header = Adw.HeaderBar()
        self.header.add_css_class("flat")
        self.root_box.append(self.header)

        # Toast overlay 用于操作结果提示
        self.toast_overlay = Adw.ToastOverlay()
        self.root_box.append(self.toast_overlay)

        # Stack 切换主页与操作页
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.toast_overlay.set_child(self.stack)

        self._build_home_page()
        self._build_empty_op_page()

        self.connect("close-request", self._on_close)

        # 若由 Nautilus 右键菜单带参启动，直接进入二级界面
        if initial_request is not None:
            self._enter_operation(initial_request)

    # ---------- 主页 ----------
    def _build_home_page(self) -> None:
        # 使用 ScrolledWindow 作为页面根容器，确保内容可滚动
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        # 使用 Clamp 限制最大宽度，放在 ScrolledWindow 内部
        clamp = Adw.Clamp(maximum_size=760)
        clamp.set_margin_top(48)
        clamp.set_margin_bottom(48)
        scrolled.set_child(clamp)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(outer)

        # 标题
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title_box.set_halign(Gtk.Align.CENTER)
        title_label = Gtk.Label(label=_("中书省"))
        title_label.add_css_class("title-1")
        subtitle_label = Gtk.Label(label=_("非主目录的文件/文件夹管理工具"))
        subtitle_label.add_css_class("dim-label")
        title_box.append(title_label)
        title_box.append(subtitle_label)
        outer.append(title_box)

        # 功能网格 3x2
        grid = Gtk.Grid()
        grid.set_row_spacing(18)
        grid.set_column_spacing(18)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_margin_top(12)

        for idx, (op, label, icon) in enumerate(OPERATION_LABELS):
            row = idx // 3
            col = idx % 3
            grid.attach(self._make_home_button(op, label, icon), col, row, 1, 1)
        outer.append(grid)

        # 说明文字
        hint = Gtk.Label(
            label=_("点击任一功能进入二级操作界面：选择目标 → 行相关操作 → 输入密码 → 完成")
        )
        hint.set_wrap(True)
        hint.add_css_class("dim-label")
        hint.set_halign(Gtk.Align.CENTER)
        outer.append(hint)

        # 语言切换和字体粗细切换按钮（放在主页底部）
        self._build_settings_switcher(outer)

        self.stack.add_named(scrolled, "home")

    def _build_settings_switcher(self, outer_box) -> None:
        """在页面底部添加语言切换和字体粗细切换按钮。"""
        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        settings_box.set_halign(Gtk.Align.CENTER)
        settings_box.set_margin_top(24)
        settings_box.set_margin_bottom(16)

        # 语言切换
        lang_frame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lang_label = Gtk.Label(label=_("语言:"))
        lang_label.add_css_class("dim-label")
        lang_frame.append(lang_label)

        current_lang = get_current_language()
        for lang_code, lang_name in get_available_languages():
            btn = Gtk.Button(label=lang_name)
            btn.add_css_class("flat")
            if lang_code == current_lang:
                btn.add_css_class("suggested-action")
            btn.connect("clicked", self._on_language_change, lang_code)
            lang_frame.append(btn)

        settings_box.append(lang_frame)

        # 分隔符
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator.set_margin_start(8)
        separator.set_margin_end(8)
        settings_box.append(separator)

        # 字体粗细切换
        font_frame = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        font_label = Gtk.Label(label=_("字体:"))
        font_label.add_css_class("dim-label")
        font_frame.append(font_label)

        current_weight = get_font_weight()
        for weight_code, weight_name in get_available_font_weights():
            btn = Gtk.Button(label=weight_name)
            btn.add_css_class("flat")
            if weight_code == current_weight:
                btn.add_css_class("suggested-action")
            btn.connect("clicked", self._on_font_weight_change, weight_code)
            font_frame.append(btn)

        settings_box.append(font_frame)

        outer_box.append(settings_box)

    def _on_language_change(self, _btn, lang_code: str) -> None:
        """语言切换回调。"""
        set_language(lang_code)
        # 重建主页以应用新语言
        self._rebuild_home_page()

    def _on_font_weight_change(self, _btn, weight_code: str) -> None:
        """字体粗细切换回调。"""
        set_font_weight(weight_code)
        # 应用字体粗细 CSS
        self._apply_font_weight()

    def _apply_font_weight(self) -> None:
        """应用字体粗细 CSS 到全局。"""
        css_content = apply_font_weight_css()
        provider = Gtk.CssProvider()
        provider.load_from_data(css_content.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,  # 高于主题 CSS
        )

    def _rebuild_home_page(self) -> None:
        """重建主页以应用语言变更。"""
        # 移除旧的 home 页面
        old_home = self.stack.get_child_by_name("home")
        if old_home:
            self.stack.remove(old_home)

        # 重新构建主页
        self._build_home_page()
        self.stack.set_visible_child_name("home")

    def _make_home_button(self, op: str, label: str, icon_name: str) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("card")
        btn.add_css_class("zhongshu-tile")
        btn.set_size_request(220, 150)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(40)
        lbl = Gtk.Label(label=label)
        lbl.add_css_class("heading")

        box.append(icon)
        box.append(lbl)
        btn.set_child(box)
        btn.connect("clicked", lambda *_: self._enter_empty_operation(op))
        return btn

    # ---------- 空白操作页占位（实际页由 _enter_operation 动态替换） ----------
    def _build_empty_op_page(self) -> None:
        self.stack.add_named(Adw.Bin(), "op")

    # ---------- 导航 ----------
    def _replace_op_page(self, view: "OperationView") -> None:
        """替换 Stack 中名为 'op' 的子页。

        Gtk4 的 Gtk.Stack 没有原生的 replace_named_child 方法，
        因此先取出现有 child 再添加新的，并复用同一个名字。
        """
        existing = self.stack.get_child_by_name("op")
        if existing is not None:
            self.stack.remove(existing)
        self.stack.add_named(view, "op")

    def _enter_empty_operation(self, op: str) -> None:
        view = OperationView(op, None, on_back=self._back_home,
                             toast_overlay=self.toast_overlay)
        self._replace_op_page(view)
        self.stack.set_visible_child_name("op")

    def _enter_operation(self, req) -> None:
        # 由 CLI 参数进入：直接进入视图，路径已填充
        view = OperationView(req.operation, req, on_back=self._back_home,
                             toast_overlay=self.toast_overlay)
        self._replace_op_page(view)
        self.stack.set_visible_child_name("op")

    def _back_home(self) -> bool:
        self.stack.set_visible_child_name("home")
        return True

    def show_toast(self, title: str, error: bool = False) -> None:
        toast = Adw.Toast(title=title)
        if error:
            toast.add_css_class("error")
        self.toast_overlay.add_toast(toast)

    def _on_close(self, *_):
        return False
