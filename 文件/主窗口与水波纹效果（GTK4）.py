# src/window.py
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GObject, Gdk

class RippleButton(Gtk.Button):
    """带有点击波纹效果的按钮"""
    def __init__(self, label, icon_name, color_class):
        super().__init__()
        self.add_css_class(color_class)
        self.add_css_class("ripple-button")
        self.set_size_request(200, 150)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(48)

        label_widget = Gtk.Label(label=label)
        label_widget.add_css_class("heading")

        box.append(icon)
        box.append(label_widget)
        self.set_child(box)

        # 点击动画连接
        self.connect("clicked", self._on_clicked)

    def _on_clicked(self, button):
        # 触发自定义信号，通知主窗口执行水波纹扩散
        self.emit("ripple-start")

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_default_size(800, 600)
        self.set_title("中书省")

        # 主容器
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        # 标题头
        header = Adw.HeaderBar()
        self.main_box.append(header)

        # 内容区域（可切换）
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_box.append(self.content_stack)

        # 主页（功能网格）
        self.home_grid = self._create_home_grid()
        self.content_stack.add_named(self.home_grid, "home")

        # 操作视图（动态创建）
        self.operation_view = None

    def _create_home_grid(self):
        grid = Gtk.Grid()
        grid.set_row_spacing(20)
        grid.set_column_spacing(20)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)
        grid.set_margin_top(50)

        # 五个功能按钮
        operations = [
            ("授予运行权限", "system-run", "permission-btn", self._on_permission),
            ("移动到", "folder-move", "move-btn", self._on_move),
            ("删除", "user-trash", "delete-btn", self._on_delete),
            ("新建文件夹", "folder-new", "new-folder-btn", self._on_new_folder),
            ("重命名", "document-edit", "rename-btn", self._on_rename)
        ]

        for i, (label, icon, css, callback) in enumerate(operations):
            btn = RippleButton(label, icon, css)
            btn.connect("clicked", callback)
            grid.attach(btn, i % 3, i // 3, 1, 1)

        return grid

    def _animate_ripple_and_switch(self, widget, operation_name):
        """执行水波纹扩散动画并切换界面"""
        # 创建全屏遮罩层模拟水波纹
        overlay = Gtk.Overlay()

        # 获取按钮在窗口中的位置（简化版，实际需要计算坐标）
        ripple = Gtk.DrawingArea()
        ripple.set_draw_func(self._draw_ripple, None)
        overlay.add_overlay(ripple)

        # 这里应该实现实际的CSS动画或Gtk动画
        # 简化演示：直接切换
        self._show_operation_view(operation_name)

    def _show_operation_view(self, operation_type, target_path=None):
        """显示具体操作界面"""
        from operation_view import OperationView
        self.operation_view = OperationView(operation_type, target_path)
        self.content_stack.add_named(self.operation_view, "operation")
        self.content_stack.set_visible_child(self.operation_view)