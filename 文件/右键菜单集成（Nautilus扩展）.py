# nautilus-extension/zhongshu-menu.py
from gi.repository import Nautilus, GObject
import subprocess

class ZhongshuMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass

    def get_file_items(self, *args):
        files = args[-1]  # 适配不同Nautilus版本
        if len(files) != 1:
            return []

        file = files[0]
        if file.get_uri_scheme() != 'file':
            return []

        # 创建顶级菜单
        menu_item = Nautilus.MenuItem(
            name="ZhongshuMenu::Open",
            label="使用中书省操作",
            tip="使用中书省进行高级文件操作"
        )

        # 创建子菜单
        submenu = Nautilus.Menu()
        menu_item.set_submenu(submenu)

        # 五项操作
        operations = [
            ("授予运行权限", self._grant_permission),
            ("移动到...", self._move_file),
            ("删除（系统目录）", self._delete_file),
            ("新建文件夹", self._new_folder),
            ("重命名", self._rename_file)
        ]

        for label, callback in operations:
            item = Nautilus.MenuItem(
                name=f"ZhongshuMenu::{label}",
                label=label
            )
            item.connect('activate', callback, file)
            submenu.append_item(item)

        return [menu_item]

    def _grant_permission(self, menu, file):
        path = file.get_location().get_path()
        subprocess.Popen(["zhongshu-app", "--operation=permission", "--path", path])

    def _move_file(self, menu, file):
        path = file.get_location().get_path()
        subprocess.Popen(["zhongshu-app", "--operation=move", "--path", path])

    def _delete_file(self, menu, file):
        path = file.get_location().get_path()
        subprocess.Popen(["zhongshu-app", "--operation=delete", "--path", path])

    def _new_folder(self, menu, file):
        path = file.get_location().get_path()
        subprocess.Popen(["zhongshu-app", "--operation=new_folder", "--parent", path])

    def _rename_file(self, menu, file):
        path = file.get_location().get_path()
        subprocess.Popen(["zhongshu-app", "--operation=rename", "--path", path])