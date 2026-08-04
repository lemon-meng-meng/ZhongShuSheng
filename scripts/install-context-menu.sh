#!/usr/bin/env bash
# scripts/install-context-menu.sh —— 中书省右键菜单部署脚本
#
# 用途：为 Nautilus / GNOME Files 安装「使用中书省操作」右键菜单。
#
# 三种使用场景：
#
#   1. AppImage 用户（无需 sudo，最常见）：
#      ./scripts/install-context-menu.sh --appimage /绝对/路径/zhongshu-x86_64.AppImage
#      ↑ 也可让 AppImage 自身调用本脚本： zhongshu-x86_64.AppImage --install-context-menu
#
#   2. deb 用户：安装 deb 后默认会写入 /usr/share/nautilus-python/extensions，
#      因此无需再手动运行本脚本。如仍想以 user 模式覆盖，可：
#      ./scripts/install-context-menu.sh                 # 检测到 /usr/bin/zhongshu-app 后即以安装模式部署
#      sudo ./scripts/install-context-menu.sh --system    # 强制系统级安装
#
#   3. 源码树开发运行：
#      bash scripts/install-context-menu.sh --appimage dist/zhongshu-x86_64.AppImage
#        或
#      bash scripts/install-context-menu.sh   # 退化为「已安装」模式
#
#   卸载：
#      ./scripts/install-context-menu.sh --uninstall
#      sudo ./scripts/install-context-menu.sh --uninstall --system
#
# 部署内容：
#   - Nautilus 扩展（zhongshu_menu.py）写入扩展目录
#   - 启动器（user 模式下指向 AppImage 或系统 /usr/bin/zhongshu-app）写入 bin 目录
#   - AppImage 路径记录到 ~/.config/zhongshu/appimage.path
#   - 启动器路径记录到 ~/.config/zhongshu/launcher.path
#
# 环境：Ubuntu 22.04+ / GNOME 43+，需要 python3-nautilus。

set -e

APP_ID="com.zhongshu.provinces"
APP_NAME="zhongshu"

# 默认安装到用户目录，--system 切换到系统目录
SCOPE="user"
APPIMAGE_PATH=""
ACTION="install"
FORCE_SYSTEM_EXT=""

# 当前脚本所在目录（源码树内或 AppImage 内部）
SELF="$(cd "$(dirname "$0")" && pwd)"

# 解析参数
while [ "$#" -gt 0 ]; do
    case "$1" in
        --appimage)
            APPIMAGE_PATH="$2"; shift 2 ;;
        --system)
            SCOPE="system"; shift ;;
        --uninstall|-u)
            ACTION="uninstall"; shift ;;
        --help|-h)
            cat <<'EOF'
中书省右键菜单部署脚本
用法：
  安装（AppImage）：  install-context-menu.sh --appimage /path/to/zhongshu.AppImage
  安装（deb/已安装）： install-context-menu.sh
  系统级安装（需root）： sudo install-context-menu.sh --system
  卸载：              install-context-menu.sh --uninstall
                       sudo install-context-menu.sh --uninstall --system
EOF
            exit 0 ;;
        *)
            echo "未知参数: $1" >&2; exit 2 ;;
    esac
done

# 选定路径
if [ "$SCOPE" = "system" ]; then
    NAUT_EXT_DIR="/usr/share/nautilus-python/extensions"
    NAUT_SCRIPT_DIR="/usr/share/nautilus/scripts"
    BIN_DIR="/usr/local/bin"
    CONFIG_DIR="/etc/zhongshu"
else
    NAUT_EXT_DIR="${HOME}/.local/share/nautilus-python/extensions"
    NAUT_SCRIPT_DIR="${HOME}/.local/share/nautilus/scripts"
    BIN_DIR="${HOME}/.local/bin"
    CONFIG_DIR="${HOME}/.config/zhongshu"
fi

# 系统级安装需要 root
if [ "$SCOPE" = "system" ] && [ "$(id -u)" != "0" ]; then
    echo "系统级安装需要 root 权限，正在通过 pkexec 提权…" >&2
    exec pkexec bash "$0" "$@"
fi

# ---------- 工具函数 ----------
have_cmd() { command -v "$1" >/dev/null 2>&1; }

resolve_appimage_abs() {
    local p="$APPIMAGE_PATH"
    [ -z "$p" ] && return 1
    case "$p" in
        /*) : ;;
        *)  p="$(pwd)/$p" ;;
    esac
    if [ ! -f "$p" ]; then
        echo "AppImage 不存在: $p" >&2
        return 1
    fi
    APPIMAGE_PATH="$(readlink -f -- "$p")"
}

# 自动从环境探测 AppImage 自身路径（仅在 --appimage 未显式传时使用）
detect_appimage_from_env() {
    local p
    for v in ZHONGSHU_APPIMAGE APPIMAGE ZHONGSHU_LAUNCHER; do
        p="${!v:-}"
        [ -z "$p" ] && continue
        # ZHONGSHU_LAUNCHER 可能是 bin/zhongshu-app；只取以 .AppImage 结尾的
        case "$p" in
            *.AppImage)
                [ -f "$p" ] || continue
                APPIMAGE_PATH="$(readlink -f -- "$p")"
                return 0 ;;
        esac
    done
    return 1
}

# 找到要复制的 Nautilus 扩展源文件
find_extension_source() {
    local f
    for f in \
        "$SELF/../nautilus-extension/zhongshu_menu.py" \
        "$SELF/nautilus-extension/zhongshu_menu.py" \
        "$SELF/../usr/share/nautilus-python/extensions/zhongshu_menu.py" \
        "$SELF/../share/nautilus-python/extensions/zhongshu_menu.py" \
        "$SELF/../../nautilus-python/extensions/zhongshu_menu.py" \
        "$SELF/../../share/nautilus-python/extensions/zhongshu_menu.py" \
        "$APPDIR/usr/share/nautilus-python/extensions/zhongshu_menu.py" \
        "/usr/share/nautilus-python/extensions/zhongshu_menu.py" \
        "/opt/zhongshu/nautilus-extension/zhongshu_menu.py"
    do
        if [ -n "$f" ] && [ -f "$f" ]; then
            EXTENSION_SOURCE="$(readlink -f -- "$f")"
            return 0
        fi
    done
    return 1
}

# 找到要复制的 Nautilus 桌面脚本
find_nautilus_script_source() {
    local f
    for f in \
        "$SELF/zhongshu-nautilus-script.sh" \
        "$SELF/../scripts/zhongshu-nautilus-script.sh" \
        "$SELF/../../share/zhongshu/scripts/zhongshu-nautilus-script.sh" \
        "$SELF/../usr/share/zhongshu/scripts/zhongshu-nautilus-script.sh" \
        "$APPDIR/usr/share/zhongshu/scripts/zhongshu-nautilus-script.sh" \
        "/opt/zhongshu/scripts/zhongshu-nautilus-script.sh"
    do
        if [ -n "$f" ] && [ -f "$f" ]; then
            NAUTILUS_SCRIPT_SOURCE="$(readlink -f -- "$f")"
            return 0
        fi
    done
    return 1
}

# 写启动器：根据部署模式生成不同的 zhongshu-app 脚本
write_launcher() {
    mkdir -p "$BIN_DIR"
    local target="$BIN_DIR/zhongshu-app"
    if [ -n "$APPIMAGE_PATH" ]; then
        # AppImage 模式：启动器把参数转发给 AppImage
        cat >"$target" <<EOF
#!/bin/sh
# 由中书省右键菜单部署脚本自动生成（AppImage 模式）。
# AppImage 真实路径已固定，便于 Nautilus 在任意环境调用。
export ZHONGSHU_LAUNCHER="$APPIMAGE_PATH"
exec "$APPIMAGE_PATH" "\$@"
EOF
        chmod +x "$target"
        mkdir -p "$CONFIG_DIR"
        printf '%s\n' "$APPIMAGE_PATH" >"$CONFIG_DIR/appimage.path"
        printf '%s\n' "$BIN_DIR/zhongshu-app"  >"$CONFIG_DIR/launcher.path"
        echo "    启动器 → $target"
        echo "        指向 AppImage： $APPIMAGE_PATH"
    elif [ -x /usr/bin/zhongshu-app ]; then
        # deb/已安装模式：user 模式下写一个转发到系统 zhongshu-app 的启动器，
        # 让 Nautilus 扩展能在一处解析；系统模式直接跳过（系统已具备 /usr/bin/zhongshu-app）
        if [ "$SCOPE" = "user" ]; then
            cat >"$target" <<'EOF'
#!/bin/sh
# 由中书省右键菜单部署脚本自动生成（已安装模式）。
exec /usr/bin/zhongshu-app "$@"
EOF
            chmod +x "$target"
            mkdir -p "$CONFIG_DIR"
            printf '%s\n' "$BIN_DIR/zhongshu-app" >"$CONFIG_DIR/launcher.path"
            rm -f "$CONFIG_DIR/appimage.path"
            echo "    启动器 → $target"
            echo "        转发到系统 /usr/bin/zhongshu-app"
        else
            echo "    系统级已具备 /usr/bin/zhongshu-app，无需额外启动器"
            rm -f "$CONFIG_DIR/appimage.path"
            printf '/usr/bin/zhongshu-app\n' >"$CONFIG_DIR/launcher.path"
        fi
    else
        echo "错误：未传 --appimage 参数，且未检测到系统 zhongshu-app 启动器。" >&2
        echo "   AppImage 用户请使用： $0 --appimage /path/to/zhongshu-x86_64.AppImage" >&2
        echo "   deb 用户请先安装 zhongshu 包： sudo apt-get install -y ./dist/zhongshu_*.deb" >&2
        exit 3
    fi
}

# 把元信息写入配置目录（扩展自诊断 + 卸载用）
write_ext_meta() {
    mkdir -p "$CONFIG_DIR"
    cat >"$CONFIG_DIR/context-menu.env" <<EOF
# 中书省右键菜单部署元信息 —— 由 install-context-menu.sh 写入
SCOPE=$SCOPE
LAUNCHER=$BIN_DIR/zhongshu-app
APPIMAGE=$APPIMAGE_PATH
EXTENSION_DIR=$NAUT_EXT_DIR
NAUTILUS_SCRIPT_DIR=$NAUT_SCRIPT_DIR
EOF
}

# ---------- 依赖检查 ----------
check_nautilus_python() {
    if ! python3 -c "import gi; gi.require_version('Nautilus','4.0')" 2>/dev/null \
       && ! python3 -c "import gi; gi.require_version('Nautilus','3.0')" 2>/dev/null; then
        echo "警告：未检测到 Nautilus 的 Python 扩展支持。" >&2
        echo "请安装：sudo apt-get install -y python3-nautilus" >&2
        echo "以及： gir1.2-nautilus-4.0 或 gir1.2-nautilus-3.0" >&2
        echo "（仍可继续部署，文件被复制到位但 Nautilus 重启后才会加载）" >&2
    fi
}

# ---------- 主流程 ----------
do_install() {
    echo "==> 部署中书省右键菜单（scope=$SCOPE）"

    if [ -z "$APPIMAGE_PATH" ]; then
        detect_appimage_from_env && echo "    自动探测到 AppImage： $APPIMAGE_PATH"
    fi
    resolve_appimage_abs || true

    if [ -z "$APPIMAGE_PATH" ]; then
        if [ -x /usr/bin/zhongshu-app ] || [ -x /usr/local/bin/zhongshu-app ]; then
            echo "    检测到已安装的 zhongshu 启动器，将以已安装模式部署"
            APPIMAGE_PATH=""
        else
            # 尝试自动发现 dist/ 下的 AppImage
            for candidate in \
                "$SELF/../dist/zhongshu-x86_64.AppImage" \
                "$SELF/../dist/zhongshu-$(uname -m).AppImage" \
                "$SELF/../../dist/zhongshu-x86_64.AppImage" \
                "$SELF/../../dist/zhongshu-$(uname -m).AppImage" \
                "$(pwd)/dist/zhongshu-x86_64.AppImage" \
                "$(pwd)/dist/zhongshu-$(uname -m).AppImage"; do
                if [ -f "$candidate" ] && [ -x "$candidate" ]; then
                    echo "    自动探测到 AppImage： $candidate"
                    APPIMAGE_PATH="$(readlink -f -- "$candidate")"
                    break
                fi
            done
        fi
        if [ -z "$APPIMAGE_PATH" ] && [ ! -x /usr/bin/zhongshu-app ] && [ ! -x /usr/local/bin/zhongshu-app ]; then
            echo "错误：未传 --appimage 参数，也未检测到 zhongshu-app 启动器。" >&2
            echo "   AppImage 用户请使用： $0 --appimage /path/to/zhongshu-x86_64.AppImage" >&2
            echo "   deb  用户请先安装 zhongshu 包： sudo apt-get install -y ./dist/zhongshu_*.deb" >&2
            exit 3
        fi
    fi

    check_nautilus_python

    echo "==> 写入启动器"
    write_launcher

    echo "==> 复制 Nautilus 扩展"
    # 系统模式 + deb 已在 /usr/share 安装了扩展，跳过重复安装（除非 --force-system-ext）
    if [ "$SCOPE" = "system" ] && [ -f /usr/share/nautilus-python/extensions/zhongshu_menu.py ] \
       && [ -z "$FORCE_SYSTEM_EXT" ]; then
        echo "    系统级扩展已由 deb 安装到位，跳过重复写入"
    else
        if ! find_extension_source; then
            echo "错误：未找到 Nautilus 扩展源文件 zhongshu_menu.py" >&2
            echo "   请在源码树内运行；或确保 /usr/share/nautilus-python/extensions/zhongshu_menu.py 存在" >&2
            exit 4
        fi
        mkdir -p "$NAUT_EXT_DIR"
        install -m0644 "$EXTENSION_SOURCE" "$NAUT_EXT_DIR/zhongshu_menu.py"
        echo "    扩展 → $NAUT_EXT_DIR/zhongshu_menu.py"
    fi

    echo "==> 部署 Nautilus 桌面脚本（用于桌面右键菜单）"
    if find_nautilus_script_source; then
        mkdir -p "$NAUT_SCRIPT_DIR"
        install -m0755 "$NAUTILUS_SCRIPT_SOURCE" "$NAUT_SCRIPT_DIR/中书省"
        echo "    桌面脚本 → $NAUT_SCRIPT_DIR/中书省"
    else
        echo "    未找到桌面脚本源文件，跳过"
    fi

    write_ext_meta

    echo "==> 重启 Nautilus 使右键菜单生效"
    if have_cmd nautilus; then
        nautilus -q 2>/dev/null || true
    fi
    if have_cmd gnome-files; then
        gnome-files -q 2>/dev/null || true
    fi

    echo
    echo "部署完成！"
    echo "  · 启动器：        $BIN_DIR/zhongshu-app"
    echo "  · Nautilus 扩展： $NAUT_EXT_DIR/zhongshu_menu.py"
    echo "  · 桌面右键脚本：  $NAUT_SCRIPT_DIR/中书省"
    if [ -n "$APPIMAGE_PATH" ]; then
        echo "  · AppImage 路径已记录： $CONFIG_DIR/appimage.path"
    fi
    echo
    echo "提示：如果右键菜单未出现，请重新打开 Nautilus 或注销重登。"
    echo "桌面右键使用方式：在桌面或文件上右键 → 中书省（桌面支持） → 选择操作"
    if [ "$SCOPE" = "user" ] && ! echo ":$PATH:" | grep -q ":$BIN_DIR:"; then
        echo "注意：$BIN_DIR 当前不在 PATH 中。Nautilus 扩展使用绝对路径调用启动器，不影响使用。"
    fi
}

do_uninstall() {
    echo "==> 卸载中书省右键菜单（scope=$SCOPE）"
    local launcher=""
    if [ -f "$CONFIG_DIR/launcher.path" ]; then
        launcher="$(cat "$CONFIG_DIR/launcher.path" 2>/dev/null || true)"
    fi
    [ -z "$launcher" ] && launcher="$BIN_DIR/zhongshu-app"

    if [ -f "$launcher" ]; then
        echo "    删除启动器 $launcher"
        rm -f "$launcher"
    fi
    # 只在 launcher.path 指向我们自己生成的启动器时才删除（避免误删 deb 安装的 /usr/bin/zhongshu-app）
    if [ -f "$NAUT_EXT_DIR/zhongshu_menu.py" ]; then
        echo "    删除扩展 $NAUT_EXT_DIR/zhongshu_menu.py"
        rm -f "$NAUT_EXT_DIR/zhongshu_menu.py"
    fi
    if [ -f "$NAUT_SCRIPT_DIR/中书省" ]; then
        echo "    删除桌面脚本 $NAUT_SCRIPT_DIR/中书省"
        rm -f "$NAUT_SCRIPT_DIR/中书省"
    fi
    rm -f "$CONFIG_DIR/appimage.path" "$CONFIG_DIR/launcher.path" "$CONFIG_DIR/context-menu.env"
    rmdir "$CONFIG_DIR" 2>/dev/null || true

    if have_cmd nautilus; then
        nautilus -q 2>/dev/null || true
    fi
    echo "卸载完成。"
}

case "$ACTION" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
esac
