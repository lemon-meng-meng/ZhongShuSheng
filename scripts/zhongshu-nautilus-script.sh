#!/usr/bin/env bash
# 中书省 Nautilus 脚本 - 用于桌面右键菜单
# 放在 ~/.local/share/nautilus/scripts/ 下即可在桌面右键使用

ZHONGSHU_LAUNCHER=$(cat "$HOME/.config/zhongshu/launcher.path" 2>/dev/null || true)
[ -z "$ZHONGSHU_LAUNCHER" ] && ZHONGSHU_LAUNCHER=$(command -v zhongshu-app 2>/dev/null || true)
[ -z "$ZHONGSHU_LAUNCHER" ] && ZHONGSHU_LAUNCHER="/usr/bin/zhongshu-app"
[ ! -x "$ZHONGSHU_LAUNCHER" ] && exec zenity --error --text="未找到中书省启动器，请先安装中书省"

ACTION=$(zenity --list --title="中书省" --text="选择操作" \
    --column="操作" --column="说明" \
    "授予运行权限" "为文件添加可执行权限" \
    "移动到" "将文件/文件夹移动到指定位置" \
    "删除" "删除文件/文件夹" \
    "新建文件夹" "在当前位置新建文件夹" \
    "新建文件" "在当前位置新建文件" \
    "重命名" "重命名文件/文件夹" \
    --width=400 --height=350 2>/dev/null)

[ -z "$ACTION" ] && exit 0

case "$ACTION" in
    "授予运行权限")
        "$ZHONGSHU_LAUNCHER" --operation=permission --path="$1"
        ;;
    "移动到")
        "$ZHONGSHU_LAUNCHER" --operation=move --path="$1"
        ;;
    "删除")
        "$ZHONGSHU_LAUNCHER" --operation=delete --path="$1"
        ;;
    "新建文件夹")
        "$ZHONGSHU_LAUNCHER" --operation=new_folder --parent="$1"
        ;;
    "新建文件")
        "$ZHONGSHU_LAUNCHER" --operation=new_file --parent="$1"
        ;;
    "重命名")
        "$ZHONGSHU_LAUNCHER" --operation=rename --path="$1"
        ;;
esac