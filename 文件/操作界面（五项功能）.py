# src/operation_view.py
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Adw, Gio, GLib

class OperationView(Gtk.Box):
    def __init__(self, operation_type, target_path=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.operation_type = operation_type
        self.target_path = target_path or ""

        # 返回按钮
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        back_btn = Gtk.Button(label="返回")
        back_btn.connect("clicked", self._on_back)
        header.append(back_btn)
        self.append(header)

        # 根据操作类型构建界面
        if operation_type == "permission":
            self._build_permission_ui()
        elif operation_type == "move":
            self._build_move_ui()
        elif operation_type == "delete":
            self._build_delete_ui()
        elif operation_type == "new_folder":
            self._build_new_folder_ui()
        elif operation_type == "rename":
            self._build_rename_ui()

    def _build_permission_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(50)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label=f"目标文件: {self.target_path}")
        box.append(label)

        info_label = Gtk.Label(label="将为该二进制文件添加可执行权限(x)")
        box.append(info_label)

        exec_btn = Gtk.Button(label="授予执行权限")
        exec_btn.add_css_class("suggested-action")
        exec_btn.connect("clicked", self._grant_permission)
        box.append(exec_btn)

        self.append(box)

    def _grant_permission(self, btn):
        # 检查是否为二进制文件
        if not self._is_binary(self.target_path):
            self._show_error("非二进制文件，无法授予运行权限")
            return

        # 弹出认证对话框执行chmod +x
        self._execute_with_auth(["chmod", "+x", self.target_path])

    def _build_move_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(50)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label=f"移动: {self.target_path}")
        box.append(label)

        # 目标选择按钮
        choose_btn = Gtk.Button(label="选择目标文件夹")
        choose_btn.connect("clicked", self._on_choose_target)
        box.append(choose_btn)

        self.target_entry = Gtk.Entry()
        self.target_entry.set_placeholder_text("目标路径（如 /opt/apps/）")
        box.append(self.target_entry)

        move_btn = Gtk.Button(label="执行移动")
        move_btn.add_css_class("suggested-action")
        move_btn.connect("clicked", self._execute_move)
        box.append(move_btn)

        self.append(box)

    def _execute_move(self, btn):
        dest = self.target_entry.get_text()
        if not dest:
            self._show_error("请选择目标文件夹")
            return

        # 检查是否为系统目录（需要提权）
        if self._is_system_path(dest):
            self._execute_with_auth(["mv", self.target_path, dest])
        else:
            # 普通目录直接移动
            self._execute_normal(["mv", self.target_path, dest])

    def _build_delete_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(50)
        box.set_halign(Gtk.Align.CENTER)

        # 风险提示
        alert = Adw.Banner(title="⚠️ 警告：将删除非/home目录下的文件")
        alert.add_css_class("warning")
        self.append(alert)

        label = Gtk.Label(label=f"待删除: {self.target_path}")
        box.append(label)

        confirm_check = Gtk.CheckButton(label="我确认了解此操作的风险")
        box.append(confirm_check)
        self.confirm_check = confirm_check

        delete_btn = Gtk.Button(label="确认删除")
        delete_btn.add_css_class("destructive-action")
        delete_btn.connect("clicked", self._execute_delete)
        box.append(delete_btn)

        self.append(box)

    def _execute_delete(self, btn):
        if not self.confirm_check.get_active():
            self._show_error("请勾选确认风险")
            return

        self._execute_with_auth(["rm", "-rf", self.target_path])

    def _build_new_folder_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(50)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label="在系统目录新建文件夹")
        box.append(label)

        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        path_box.append(Gtk.Label(label="父目录: "))
        self.parent_entry = Gtk.Entry()
        self.parent_entry.set_text("/opt")
        path_box.append(self.parent_entry)
        box.append(path_box)

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        name_box.append(Gtk.Label(label="文件夹名: "))
        self.folder_name_entry = Gtk.Entry()
        name_box.append(self.folder_name_entry)
        box.append(name_box)

        create_btn = Gtk.Button(label="创建文件夹")
        create_btn.add_css_class("suggested-action")
        create_btn.connect("clicked", self._execute_mkdir)
        box.append(create_btn)

        self.append(box)

    def _execute_mkdir(self, btn):
        parent = self.parent_entry.get_text()
        name = self.folder_name_entry.get_text()
        full_path = f"{parent}/{name}"

        self._execute_with_auth(["mkdir", "-p", full_path])

    def _build_rename_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(50)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label=f"重命名: {self.target_path}")
        box.append(label)

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        name_box.append(Gtk.Label(label="新名称: "))
        self.new_name_entry = Gtk.Entry()
        name_box.append(self.new_name_entry)
        box.append(name_box)

        rename_btn = Gtk.Button(label="执行重命名")
        rename_btn.add_css_class("suggested-action")
        rename_btn.connect("clicked", self._execute_rename)
        box.append(rename_btn)

        self.append(box)

    def _execute_rename(self, btn):
        new_name = self.new_name_entry.get_text()
        if not new_name:
            return

        import os
        dir_path = os.path.dirname(self.target_path)
        new_path = os.path.join(dir_path, new_name)

        if self._is_system_path(dir_path):
            self._execute_with_auth(["mv", self.target_path, new_path])
        else:
            self._execute_normal(["mv", self.target_path, new_path])

    def _is_binary(self, filepath):
        """检查文件是否为二进制可执行文件"""
        import magic
        try:
            file_type = magic.from_file(filepath)
            return "ELF" in file_type or "executable" in file_type
        except:
            return False

    def _is_system_path(self, path):
        """检查路径是否需要提权（非/home目录）"""
        return not path.startswith("/home/")

    def _execute_with_auth(self, command):
        """使用pkexec执行需要提权的命令"""
        try:
            # 构建pkexec命令
            cmd = ["pkexec"] + command
            proc = Gio.Subprocess.new(
                cmd,
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
            )
            proc.wait_check_async(None, self._on_command_finish)
        except Exception as e:
            self._show_error(str(e))

    def _execute_normal(self, command):
        """普通权限执行"""
        try:
            proc = Gio.Subprocess.new(
                command,
                Gio.SubprocessFlags.NONE
            )
        except Exception as e:
            self._show_error(str(e))

    def _on_command_finish(self, proc, result):
        try:
            proc.wait_check_finish(result)
            self._show_success("操作成功")
        except GLib.Error as e:
            self._show_error(f"操作失败: {e.message}")

    def _show_error(self, msg):
        dialog = Adw.MessageDialog(
            transient_for=self.get_root(),
            heading="错误",
            body=msg
        )
        dialog.add_response("ok", "确定")
        dialog.present()

    def _show_success(self, msg):
        toast = Adw.Toast(title=msg)
        # 添加到ToastOverlay...

    def _on_back(self, btn):
        # 返回主页
        window = self.get_root()
        window.content_stack.set_visible_child(window.home_grid)