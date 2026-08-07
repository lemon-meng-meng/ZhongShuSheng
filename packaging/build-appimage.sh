#!/usr/bin/env bash
# packaging/build-appimage.sh —— 在源码目录下执行，构建 AppImage
#
# 前置：
#   1. 下载对应架构的 appimagetool 到 /tmp/appimagetool.AppImage
#   2. 运行： bash packaging/build-appimage.sh [arch]
#      支持的架构：x86_64 (默认), aarch64, loongarch64
#
# 注：本 AppImage 适合「跨发行版」分发，但运行时仍需目标系统已安装
#     GTK4 + libadwaita + pkexec，因为这些库自身体积巨大不便静态打包。

set -e

HERE="$(cd "$(dirname "$0")/.." && pwd)"
APP_ID="com.zhongshu.provinces"
APPDIR="$HERE/packaging/appimage"
APPNAME_LOWER="zhongshu"
OUT_DIR="$HERE/releases"
TARGET_ARCH="${1:-$(uname -m)}"
APPIMAGE="$OUT_DIR/${APPNAME_LOWER}-${TARGET_ARCH}.AppImage"

mkdir -p "$OUT_DIR"

# ---------- 填充 AppDir ----------
USR="$APPDIR/usr"

echo "==> 复制源码与数据 (目标架构: $TARGET_ARCH)"
mkdir -p "$USR/lib/zhongshu/src/zhongshu"
mkdir -p "$USR/share/locale"
cp -r "$HERE/src/zhongshu/." "$USR/lib/zhongshu/src/zhongshu/"
cp -r "$HERE/data/." "$USR/lib/zhongshu/data/"
cp -r "$HERE/locale/." "$USR/share/locale/"

# 启动器真实脚本（与 bin/zhongshu-app 一致的入口，避免 python3 -c 导致 sys.argv[0]='-c'）
mkdir -p "$USR/lib/zhongshu"
cat > "$USR/lib/zhongshu/zhongshu-launcher" <<'EOF_LAUNCHER'
#!/usr/bin/env python3
"""AppImage 内置启动器 —— 把 src 加入 sys.path 并委托 zhongshu.app.main。"""
import os
import sys

APPDIR = os.environ.get("APPDIR", "")
SCRIPT_DIR = os.path.join(APPDIR, "usr", "lib", "zhongshu", "src")
if os.path.isdir(os.path.join(SCRIPT_DIR, "zhongshu")):
    sys.path.insert(0, SCRIPT_DIR)
elif os.path.isdir(os.path.join(os.getcwd(), "src", "zhongshu")):
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from zhongshu.app import main
raise SystemExit(main())
EOF_LAUNCHER
chmod 0755 "$USR/lib/zhongshu/zhongshu-launcher"

# 桌面
install -Dm0644 "$HERE/data/com.zhongshu.provinces.desktop" \
    "$APPDIR/$APP_ID.desktop"
install -Dm0644 "$HERE/data/com.zhongshu.provinces.desktop" \
    "$USR/share/applications/$APP_ID.desktop"

# 图标
install -Dm0644 "$HERE/data/icons/$APP_ID.png" \
    "$APPDIR/$APP_ID.png"
install -Dm0644 "$HERE/data/icons/$APP_ID.png" \
    "$USR/share/icons/hicolor/scalable/apps/$APP_ID.png"

# metainfo
install -Dm0644 "$HERE/data/$APP_ID.metainfo.xml" \
    "$USR/share/metainfo/$APP_ID.metainfo.xml"

# Nautilus 扩展（放 usr/share）
install -Dm0644 "$HERE/nautilus-extension/zhongshu_menu.py" \
    "$USR/share/nautilus-python/extensions/zhongshu_menu.py"

# 右键菜单部署脚本（供 --install-context-menu 子命令使用）
install -Dm0755 "$HERE/scripts/install-context-menu.sh" \
    "$USR/share/zhongshu/scripts/install-context-menu.sh"
# 桌面右键 Nautilus 脚本
install -Dm0755 "$HERE/scripts/zhongshu-nautilus-script.sh" \
    "$USR/share/zhongshu/scripts/zhongshu-nautilus-script.sh"
# 一键卸载脚本
install -Dm0755 "$HERE/scripts/uninstall-context-menu.sh" \
    "$USR/share/zhongshu/scripts/uninstall-context-menu.sh"

# 启动器：AppRun 调用内置 launcher python 脚本（避免 -c 导致 sys.argv[0]='-c'）
cat > "$APPDIR/AppRun" <<'EOF_APPRUN'
#!/usr/bin/env bash
# AppRun —— AppImage 入口
APPDIR="$(cd "$(dirname "$0")" && pwd)"
# 导出 APPDIR，供 app.py 内 --install-context-menu 子命令定位内置部署脚本
export APPDIR
# 记录自身路径供 Nautilus 集成可选；APPIMAGE 用于定位真实的 AppImage
export ZHONGSHU_LAUNCHER="$0"
export ZHONGSHU_APPIMAGE="${ZHONGSHU_APPIMAGE:-${APPIMAGE:-$0}}"
exec python3 "$APPDIR/usr/lib/zhongshu/zhongshu-launcher" "$@"
EOF_APPRUN
chmod 0755 "$APPDIR/AppRun"

# .DirIcon
ln -sf "$APP_ID.png" "$APPDIR/.DirIcon"

echo "==> 校验桌面文件"
if command -v desktop-file-validate >/dev/null; then
    desktop-file-validate "$APPDIR/$APP_ID.desktop" || true
fi

# 打包 ----------
# 若指定外部路径使用，否则尝试运行时下载安装
if [ -z "$APPIMAGETOOL" ]; then
    if [ -x /tmp/appimagetool.AppImage ]; then
        APPIMAGETOOL=/tmp/appimagetool.AppImage
    elif command -v appimagetool >/dev/null; then
        APPIMAGETOOL=appimagetool
    elif command -v appimagetool-x86_64 >/dev/null; then
        APPIMAGETOOL=appimagetool-x86_64
    else
        echo "找不到 appimagetool，请先安装："
        echo "  真 URL 的 asset 名带版本前缀（如 appimagetool-947-x86_64.AppImage），"
        echo "  当前最新请参见 https://github.com/probonopd/go-appimage/releases"
        echo "  示例："
        echo "    curl -L -o /tmp/appimagetool.AppImage https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-${TARGET_ARCH}.AppImage"
        echo "    chmod +x /tmp/appimagetool.AppImage"
        echo "  或： sudo apt-get install -y libfuse2   # 若无 fuse"
        exit 1
    fi
fi

echo "==> 使用 $APPIMAGETOOL 打包"
export ARCH="${ARCH:-$TARGET_ARCH}"
export VERSION="${VERSION:-0.1.1}"

# 新版 appimagetool (probonopd/go-appimage, build≥177) 使用 Cobra 风格 CLI：
#   appimagetool [--appimage-extract-and-run] <AppDir>
# 输出文件名由 AppDir 顶部 .desktop 文件中的 Name 字段决定，
# 命名为 "<Name>-<VERSION>-<ARCH>.AppImage"，生成在调用时所在目录。
# 因此我们 cd 到输出目录后再调用，并避免含中文/特殊字符的路径问题。

EXTRACT_FLAG="--appimage-extract-and-run"
if [ -w /dev/fuse ] 2>/dev/null; then
    EXTRACT_FLAG=""
fi

# 把 AppDir 复制到一个临时、无特殊字符的目录，避免 appimagetool 对中文路径敏感
TMP_APPDIR="$(mktemp -d -t zhongshu-appdir-XXXXXX)"
TMP_APPDIR_BASE="$(basename "$TMP_APPDIR")"
cp -a "$APPDIR" "$TMP_APPDIR/$TMP_APPDIR_BASE"
TMP_OUT="$(mktemp -d -t zhongshu-appimg-out-XXXXXX)"

( cd "$TMP_OUT" && "$APPIMAGETOOL" $EXTRACT_FLAG \
    "$TMP_APPDIR/$TMP_APPDIR_BASE" ) || {
        echo "appimagetool 失败（见上方日志）。"
        rm -rf "$TMP_APPDIR" "$TMP_OUT"
        exit 1
    }

# 把生成的 AppImage 移到最终输出位置
shopt -s nullglob
found=""
for ai in "$TMP_OUT"/*.AppImage; do
    mv -f "$ai" "$APPIMAGE"
    found="$ai"
done
rm -rf "$TMP_APPDIR" "$TMP_OUT"
if [ -z "$found" ]; then
    echo "appimagetool 未产生 AppImage，请检查上方日志。"
    exit 1
fi

echo
echo "完成 → $APPIMAGE"
