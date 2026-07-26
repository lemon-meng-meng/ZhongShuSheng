#!/usr/bin/env bash
# packaging/build-appimage.sh —— 在源码目录下执行，构建 zhongshu-x86_64.AppImage
#
# 前置：
#   1. 下载 appimagetool-x86_64.AppImage 到 /tmp/appimagetool.AppImage
#   2. 运行： bash packaging/build-appimage.sh
#
# 注：本 AppImage 适合「跨发行版」分发，但运行时仍需目标系统已安装
#     GTK4 + libadwaita + pkexec，因为这些库自身体积巨大不便静态打包。

set -e

HERE="$(cd "$(dirname "$0")/.." && pwd)"
APP_ID="com.zhongshu.provinces"
APPDIR="$HERE/packaging/appimage"
APPNAME_LOWER="zhongshu"
OUT_DIR="$HERE/dist"
APPIMAGE="$OUT_DIR/${APPNAME_LOWER}-$(uname -m).AppImage"

mkdir -p "$OUT_DIR"

# ---------- 填充 AppDir ----------
USR="$APPDIR/usr"

echo "==> 复制源码与数据"
mkdir -p "$USR/lib/zhongshu/src/zhongshu"
cp -r "$HERE/src/zhongshu/." "$USR/lib/zhongshu/src/zhongshu/"
cp -r "$HERE/data/." "$USR/lib/zhongshu/data/"

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

# 启动器：AppRun（依赖 appimagetool 的 shim 框架）
# 为我们的应用提供一个简单的桌面启动器
cat > "$APPDIR/AppRun" <<'EOF_APPRUN'
#!/usr/bin/env bash
# AppRun —— AppImage 入口
APPDIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$APPDIR/usr/lib/zhongshu/src"
# 记录图标 / 桌面文件位置供 Nautilus 集成可选
export ZHONGSHU_LAUNCHER="$0"
exec python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from zhongshu.app import main; raise SystemExit(main())" "$@"
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
        echo "  wget -O /tmp/appimagetool.AppImage https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-$(uname -m).AppImage"
        echo "  chmod +x /tmp/appimagetool.AppImage"
        echo "或："
        echo "  sudo apt-get install -y fuse libfuse2   # AppImage 运行需要"
        exit 1
    fi
fi

echo "==> 使用 $APPIMAGETOOL 打包"
export ARCH="${ARCH:-$(uname -m)}"
# appimagetool 13 需要 ARCH 环境变量；同时 GUI 需要 DISPLAY 或可允许 noapprun 校验。
"$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$APPIMAGE"

echo
echo "完成 → $APPIMAGE"
