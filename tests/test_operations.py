"""operations 模块基础测试。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zhongshu import operations as ops


def test_is_system_path_home():
    assert ops.is_system_path(os.path.expanduser("~/Documents/test.txt")) is False


def test_is_system_path_opt():
    assert ops.is_system_path("/opt/zhongshu") is True


def test_is_system_path_root_rejected():
    ok, _ = ops.validate_path("/", must_exist=False)
    assert not ok


def test_build_command_chmod_x():
    cmd = ops.build_command("chmod_x", path="/opt/x")
    assert cmd == ["chmod", "+x", "/opt/x"]


def test_build_command_move():
    cmd = ops.build_command("move", path="/opt/src", dest="/opt/dest")
    assert cmd == ["mv", "-f", "--", "/opt/src", "/opt/dest/src"]


def test_build_command_rm():
    cmd = ops.build_command("rm", path="/opt/x")
    assert cmd == ["rm", "-rf", "--", "/opt/x"]


def test_build_command_rename():
    cmd = ops.build_command("rename", path="/opt/a/b", new_path="/opt/a/c")
    assert cmd == ["mv", "--", "/opt/a/b", "/opt/a/c"]


def test_validate_path_empty():
    ok, _ = ops.validate_path("", must_exist=False)
    assert not ok


def test_join_path():
    assert ops.join_path("/opt", "sub") == "/opt/sub"
    assert ops.join_path("/opt/", "sub") == "/opt/sub"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS  {name}")
