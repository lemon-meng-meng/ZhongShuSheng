"""二级操作界面：包含五项功能（授予权限 / 移动 / 删除 / 新建文件夹 / 重命名 / 新建文件）的表单。
"""
from __future__ import annotations

import os
from typing import Callable, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from . import operations
from .runner import OperationRequest, OperationRunner


OP_TITLES = {
    "permission": "授予运行权限",
    "move": "移动文件 / 文件夹",
    "delete": "删除文件 / 文件夹",
    "new_folder": "新建文件夹",
    "new_file": "新建文件",
    "rename": "重命名",
}


class OperationView(Adw.Bin):
    def __init__(self, operation: str,
                 request: Optional[OperationRequest] = None,
                 on_back: Optional[Callable[[], None]] = None,
                 toast_overlay: Optional[Adw.ToastOverlay] = None):
        super().__init__()
        self.operation = operation
        self.request = request
        self.on_back = on_back
        self.toast_overlay = toast_overlay
        self._runner = OperationRunner(on_done=self._on_done)

        self._build_shell()

    # ---------- 外壳 ----------
    def _build_shell(self) -> None:
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(self._build_header())

        content = Adw.Clamp(maximum_size=720)
        content.set_margin_top(24)
        content.set_margin_bottom(24)

        if self.operation == "permission":
            content.set_child(self._build_permission_ui())
        elif self.operation == "move":
            content.set_child(self._build_move_ui())
        elif self.operation == "delete":
            content.set_child(self._build_delete_ui())
        elif self.operation == "new_folder":
            content.set_child(self._build_new_folder_ui(for_file=False))
        elif self.operation == "new_file":
            content.set_child(self._build_new_folder_ui(for_file=True))
        elif self.operation == "rename":
            content.set_child(self._build_rename_ui())
        else:
            content.set_child(Gtk.Label(label=f"未知操作: {self.operation}"))

        toolbar.set_content(content)
        self.set_child(toolbar)

    def _build_header(self) -> Adw.HeaderBar:
        hb = Adw.HeaderBar()
        back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        back_btn.set_tooltip_text("返回")
        back_btn.connect("clicked", lambda *_: self.on_back() if self.on_back else None)
        hb.pack_start(back_btn)
        title = Adw.WindowTitle(title=OP_TITLES.get(self.operation, "操作"),
                                subtitle="中书省")
        hb.set_title_widget(title)
        return hb

    # ---------- 公用：路径选择按钮 ----------
    def _make_path_row(self, default: str = "", placeholder: str = "",
                       row_title: str = "路径", directory_only: bool = False,
                       entry_name: str = "_path_entry") -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_hexpand(True)

        entry = Gtk.Entry()
        entry.set_hexpand(True)
        entry.set_text(default)
        entry.set_placeholder_text(placeholder)
        setattr(self, entry_name, entry)
        box.append(entry)

        btn = Gtk.Button(label="选择…")
        btn.connect("clicked", self._choose_path, entry, directory_only)
        box.append(btn)
        return box

    def _choose_path(self, _btn, entry: Gtk.Entry, directory_only: bool) -> None:
        filt = Gtk.FileFilter()
        filt.set_name("任意文件")
        filt.add_pattern("*")

        dialog = Gtk.FileDialog()
        dialog.set_title("选择" + ("文件夹" if directory_only else "文件"))
        if directory_only:
            # 选择文件夹
            def _handle(d, res):
                try:
                    f = d.select_folder_finish(res)
                    entry.set_text(f.get_path())
                except GLib.Error:
                    pass
            dialog.select_folder(self.get_root(), None, _handle)
        else:
            def _handle(d, res):
                try:
                    f = d.open_finish(res)
                    entry.set_text(f.get_path())
                except GLib.Error:
                    pass
            dialog.open(self.get_root(), None, _handle)

    # ---------- 授予运行权限 ----------
    def _build_permission_ui(self) -> Gtk.Box:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_halign(Gtk.Align.CENTER)

        outer.append(Gtk.Label(label="选择一个二进制文件以授予运行权限"))
        outer.append(self._make_path_row(
            default=self.request.path if self.request else "",
            placeholder="/path/to/binary",
            row_title="文件",
            directory_only=False,
            entry_name="_path_entry"))

        self._perm_info = Gtk.Label(label="")
        self._perm_info.set_wrap(True)
        self._perm_info.add_css_class("dim-label")
        outer.append(self._perm_info)

        btn = Gtk.Button(label="检测并授予运行权限")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._do_permission)
        outer.append(btn)
        return outer

    def _do_permission(self, _btn) -> None:
        path = self._path_entry.get_text().strip()
        ok, msg = operations.validate_path(path, must_exist=True)
        if not ok:
            self._show_error(msg)
            return

        is_exec, desc = operations.is_executable_binary(path)
        self._perm_info.set_text(desc)
        if not is_exec:
            self._show_error("该文件不是可执行二进制，无法授予运行权限")
            return

        use_auth = operations.needs_auth_for_target(path)
        cmd = operations.build_command("chmod_x", path=path)
        self._run_cmd(cmd, use_auth)

    # ---------- 移动 ----------
    def _build_move_ui(self) -> Gtk.Box:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_halign(Gtk.Align.CENTER)

        outer.append(Gtk.Label(label="1. 选择要移动的文件或文件夹"))
        outer.append(self._make_path_row(
            default=self.request.path if self.request else "",
            placeholder="源路径",
            row_title="源",
            directory_only=False,
            entry_name="_src_entry"))

        outer.append(Gtk.Label(label="2. 选择目标父目录（如 /opt）"))
        outer.append(self._make_path_row(
            default=self.request.dest if self.request else "",
            placeholder="/opt",
            row_title="目标",
            directory_only=True,
            entry_name="_dest_entry"))

        hint = Gtk.Label(label="如目标在系统目录（非 home），执行时会弹出密码框")
        hint.add_css_class("dim-label")
        outer.append(hint)

        btn = Gtk.Button(label="执行移动")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._do_move)
        outer.append(btn)
        return outer

    def _do_move(self, _btn) -> None:
        src = self._src_entry.get_text().strip()
        dest = self._dest_entry.get_text().strip()
        ok1, m1 = operations.validate_path(src, must_exist=True)
        if not ok1:
            self._show_error(m1)
            return
        ok2, m2 = operations.validate_path(dest, must_exist=True)
        if not ok2 or not operations.safe_is_dir(dest):
            self._show_error(m2 if not ok2 else "目标不是目录: " + dest)
            return

        cmd = operations.build_command("move", path=src, dest=dest)
        use_auth = (operations.needs_auth_for_target(src)
                    or operations.needs_auth_for_target(dest))
        self._run_cmd(cmd, use_auth)

    # ---------- 删除 ----------
    def _build_delete_ui(self) -> Gtk.Box:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_halign(Gtk.Align.CENTER)

        banner = Adw.Banner(
            title="警告：将删除非 home 主目录下的文件/文件夹",
            button_label="我已知风险，继续操作")
        banner.set_revealed(True)
        if operations.is_system_path(self.request.path if self.request else "/home"):
            banner.add_css_class("error")
        outer.append(banner)
        self._del_banner = banner

        outer.append(Gtk.Label(label="选择要删除的文件或文件夹"))
        outer.append(self._make_path_row(
            default=self.request.path if self.request else "",
            placeholder="目标路径",
            row_title="目标",
            directory_only=False,
            entry_name="_del_entry"))

        self._del_confirm = Gtk.CheckButton(label="我已确认此操作不可撤销")
        outer.append(self._del_confirm)

        btn = Gtk.Button(label="确认删除")
        btn.add_css_class("destructive-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._do_delete)
        outer.append(btn)
        return outer

    def _do_delete(self, _btn) -> None:
        if not self._del_confirm.get_active():
            self._show_error("请先勾选确认风险")
            return
        path = self._del_entry.get_text().strip()
        ok, msg = operations.validate_path(path, must_exist=True)
        if not ok:
            self._show_error(msg)
            return
        cmd = operations.build_command("rm", path=path)
        self._run_cmd(cmd, operations.needs_auth_for_target(path))

    # ---------- 新建文件夹 / 文件 ----------
    def _build_new_folder_ui(self, for_file: bool) -> Gtk.Box:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_halign(Gtk.Align.CENTER)

        label = ("新建文件" if for_file else "新建文件夹")
        outer.append(Gtk.Label(label=f"{label}：选择父目录并输入名称"))

        outer.append(Gtk.Label(label="父目录"))
        outer.append(self._make_path_row(
            default=self.request.parent if self.request else "/opt",
            placeholder="/opt 或其他系统目录",
            row_title="父目录",
            directory_only=True,
            entry_name="_parent_entry"))

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name_box.set_hexpand(True)
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("名称")
        name_entry.set_hexpand(True)
        if self.request and self.request.new_name:
            name_entry.set_text(self.request.new_name)
        self._name_entry = name_entry
        name_box.append(Gtk.Label(label="名称:"))
        name_box.append(name_entry)
        outer.append(name_box)

        btn = Gtk.Button(label=("创建文件" if for_file else "创建文件夹"))
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._do_new)
        self._new_for_file = for_file
        outer.append(btn)
        return outer

    def _do_new(self, _btn) -> None:
        parent = self._parent_entry.get_text().strip()
        name = self._name_entry.get_text().strip()
        red = "/\\:*?\"<>|"
        if not name or any(c in red for c in name) or name.startswith("."):
            self._show_error("名称为空或包含非法字符")
            return
        ok, m = operations.validate_path(parent, must_exist=True)
        if not ok or not operations.safe_is_dir(parent):
            self._show_error(m if not ok else "父目录不是目录: " + parent)
            return
        full = operations.join_path(parent, name)
        if self._new_for_file:
            cmd = ["sh", "-c", f"umask 022; > {_sh_quote(full)}"]
        else:
            cmd = operations.build_command("mkdir", path=full)
        self._run_cmd(cmd, operations.needs_auth_for_target(parent))

    # ---------- 重命名 ----------
    def _build_rename_ui(self) -> Gtk.Box:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_halign(Gtk.Align.CENTER)

        outer.append(Gtk.Label(label="选择要重命名的文件或文件夹"))
        outer.append(self._make_path_row(
            default=self.request.path if self.request else "",
            placeholder="目标路径",
            row_title="目标",
            directory_only=False,
            entry_name="_ren_entry"))

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("新名称")
        name_entry.set_hexpand(True)
        self._ren_name_entry = name_entry
        name_box.append(Gtk.Label(label="新名称:"))
        name_box.append(name_entry)
        outer.append(name_box)

        btn = Gtk.Button(label="执行重命名")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._do_rename)
        outer.append(btn)
        return outer

    def _do_rename(self, _btn) -> None:
        path = self._ren_entry.get_text().strip()
        new_name = self._ren_name_entry.get_text().strip()
        ok, m = operations.validate_path(path, must_exist=True)
        if not ok:
            self._show_error(m)
            return
        if not new_name or os.path.sep in new_name or new_name in (".", ".."):
            self._show_error("新名称无效")
            return
        new_path = operations.join_path(os.path.dirname(path), new_name)
        cmd = operations.build_command("rename", path=path, new_path=new_path)
        self._run_cmd(cmd, operations.needs_auth_for_target(path))

    # ---------- 执行 ----------
    def _run_cmd(self, cmd, use_auth: bool) -> None:
        # 由 OperationRunner 处理调度 + 提权
        final_cmd = operations.wrap_with_pkexec(cmd) if use_auth else cmd
        try:
            from gi.repository import Gio
            proc = Gio.Subprocess.new(
                final_cmd,
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            )
            proc.wait_check_async(None, self._gio_finish)
        except Exception as e:
            ok, msg = operations.run_command(cmd, use_auth)
            self._on_done(ok, msg)

    def _gio_finish(self, proc, res):
        from gi.repository import GLib
        try:
            proc.wait_check_finish(res)
            self._on_done(True, "操作成功")
        except GLib.Error as e:
            self._on_done(False, e.message or "操作失败")

    def _on_done(self, ok: bool, msg: str) -> None:
        from gi.repository import GLib
        # 回到主线程更新 UI
        GLib.idle_add(self._emit_done, ok, msg)

    def _emit_done(self, ok: bool, msg: str) -> bool:
        if ok:
            self._toast(msg or "操作成功")
        else:
            self._show_error(msg or "操作失败")
        return False

    # ---------- UI 助手 ----------
    def _toast(self, title: str) -> None:
        if self.toast_overlay:
            toast = Adw.Toast(title=title)
            self.toast_overlay.add_toast(toast)
            return
        # fallback dialog
        self._info_dialog("完成", title)

    def _show_error(self, msg: str) -> None:
        self._info_dialog("错误", msg, error=True)

    def _info_dialog(self, heading: str, body: str, error: bool = False) -> None:
        dlg = Adw.MessageDialog(transient_for=self.get_root(), heading=heading, body=body)
        dlg.add_response("ok", "确定")
        if error:
            dlg.add_css_class("error-dialog")
        dlg.present()


def _sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"
