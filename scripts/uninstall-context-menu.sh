#!/usr/bin/env bash
# 中书省一键卸载右键集成脚本
# 用法：
#   bash uninstall-context-menu.sh
#   bash uninstall-context-menu.sh --system  (系统级卸载，需要sudo)

set -e

ACTION="uninstall"
SYSTEM_MODE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --system) SYSTEM_MODE="--system"; shift ;;
        --help|-h)
            echo "用法：bash uninstall-context-menu.sh [--system]"
            echo "  --system  卸载系统级右键菜单（需要sudo权限）"
            exit 0 ;;
        *)
            echo "未知参数: $1"; exit 2 ;;
    esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"

# 优先查找 install-context-menu.sh（卸载功能内置于其中）
CANDIDATES=(
    "$HERE/install-context-menu.sh"
    "$HERE/../scripts/install-context-menu.sh"
    "$HERE/../usr/share/zhongshu/scripts/install-context-menu.sh"
    "$(dirname "$HERE")/scripts/install-context-menu.sh"
    "/opt/zhongshu/scripts/install-context-menu.sh"
)

MAIN_SCRIPT=""
for c in "${CANDIDATES[@]}"; do
    if [ -n "$c" ] && [ -f "$c" ]; then
        MAIN_SCRIPT="$(readlink -f "$c")"
        break
    fi
done

if [ -z "$MAIN_SCRIPT" ]; then
    echo "未找到 install-context-menu.sh，请确保在源码树或已安装目录中运行。"
    echo "尝试从 /opt/zhongshu 查找..."
    if [ -x /opt/zhongshu/scripts/install-context-menu.sh ]; then
        MAIN_SCRIPT="/opt/zhongshu/scripts/install-context-menu.sh"
    fi
fi

if [ -n "$SYSTEM_MODE" ] && [ "$(id -u)" != "0" ]; then
    echo "系统级卸载需要 root 权限，使用 pkexec 提权..."
    exec pkexec bash "$0" --system
fi

echo "=== 中书省右键菜单卸载 ===

要卸载的内容：
  · Nautilus Python 扩展（zhongshu_menu.py）
  · Nautilus 桌面脚本（中书省）
  · 中书省启动器（~/.local/bin/zhongshu-app）
  · 配置文件（~/.config/zhongshu/）

"

# 卸载 Nautilus Python 扩展
if [ -n "$SYSTEM_MODE" ]; then
    NAUT_EXT="/usr/share/nautilus-python/extensions/zhongshu_menu.py"
else
    NAUT_EXT="$HOME/.local/share/nautilus-python/extensions/zhongshu_menu.py"
fi
if [ -f "$NAUT_EXT" ]; then
    echo "  删除 Nautilus 扩展: $NAUT_EXT"
    rm -f "$NAUT_EXT"
fi

# 卸载 Nautilus 桌面脚本
if [ -n "$SYSTEM_MODE" ]; then
    NAUT_SCRIPT="/usr/share/nautilus/scripts/中书省"
else
    NAUT_SCRIPT="$HOME/.local/share/nautilus/scripts/中书省"
fi
if [ -f "$NAUT_SCRIPT" ]; then
    echo "  删除 Nautilus 桌面脚本: $NAUT_SCRIPT"
    rm -f "$NAUT_SCRIPT"
fi

# 卸载启动器和配置
if [ -n "$SYSTEM_MODE" ]; then
    rm -f /etc/zhongshu/launcher.path
    rm -f /etc/zhongshu/appimage.path
    rm -f /etc/zhongshu/context-menu.env
    rmdir /etc/zhongshu 2>/dev/null || true
else
    rm -f "$HOME/.local/bin/zhongshu-app"
    rm -f "$HOME/.config/zhongshu/launcher.path"
    rm -f "$HOME/.config/zhongshu/appimage.path"
    rm -f "$HOME/.config/zhongshu/context-menu.env"
    rmdir "$HOME/.config/zhongshu" 2>/dev/null || true
fi

# 重启 Nautilus
if command -v nautilus >/dev/null 2>&1; then
    nautilus -q 2>/dev/null || true
fi

echo ""
echo "==== 卸载完成！===="
echo "右键菜单已从以下位置移除："
echo "  · Nautilus Python 扩展: $NAUT_EXT"
echo "  · Nautilus 桌面脚本: $NAUT_SCRIPT"
echo ""
echo "注销后重新登录即可完全清除痕迹。"