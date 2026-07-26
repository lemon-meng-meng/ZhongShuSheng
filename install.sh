#!/bin/bash
# install.sh —— 在源码目录下执行，进行打包装机测试。
#
# 用途：
#   1. 将 zhongshu 源码安装到 /opt/zhongshu
#   2. 在 /usr/bin/zhongshu-app 创建启动器
#   3. 安装 .desktop / 图标 / metainfo
#   4. 安装 Nautilus 扩展到系统目录
#
# 运行： bash install.sh     或     sudo bash install.sh
# 卸载： sudo bash install.sh --uninstall

set -e

APP_ID="com.zhongshu.provinces"
PREFIX="$(pwd)"

PREFIX_DEST="/opt/zhongshu"
BIN_DEST="/usr/bin/zhongshu-app"
NAUT_EXT_DIR="/usr/share/nautilus-python/extensions"
APP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor"
METAINFO_DIR="/usr/share/metainfo"

require_root() {
    if [ "$(id -u)" != "0" ]; then
        echo "需要 root 权限，正在请求提权…"
        exec pkexec bash "$0" "$@"
    fi
}

install_deps() {
    local pkgs="python3-gi python3-nautilus gir1.2-gtk-4.0 gir1.2-libadwaita-1
                python3-magic libmagic1"
    local missing=()
    for p in $pkgs; do
        if ! dpkg -s "$p" >/dev/null 2>&1; then
            missing+=("$p")
        fi
    done
    if [ "${#missing[@]}" -gt 0 ]; then
        echo "缺少依赖包: ${missing[*]}"
        echo "执行: apt-get install -y ${missing[*]}"
        apt-get update -qq
        apt-get install -y "${missing[@]}"
    fi
}

do_install() {
    require_root
    install_deps

    echo "==> 安装源码到 $PREFIX_DEST"
    mkdir -p "$PREFIX_DEST"
    cp -a src "$PREFIX_DEST/src"
    cp -a data "$PREFIX_DEST/data"

    echo "==> 创建启动器 $BIN_DEST"
    cat > "$BIN_DEST" <<'EOF'
#!/bin/sh
# 由 zhongshu install.sh 生成
exec python3 -c 'import sys; sys.path.insert(0, "/opt/zhongshu/src"); from zhongshu.app import main; sys.exit(main())' "$@"
EOF
    chmod 0755 "$BIN_DEST"

    echo "==> 安装 .desktop"
    desktop-file-install \
        --dir="$APP_DIR" \
        --set-icon="$APP_ID" \
        --set-key=Icon --set-value="$APP_ID" \
        "$PREFIX/data/com.zhongshu.provinces.desktop"

    echo "==> 安装图标"
    install -Dm0644 "$PREFIX/data/icons/$APP_ID.png" \
        "$ICON_DIR/scalable/apps/$APP_ID.png"
    gtk-update-icon-cache -f "$ICON_DIR" 2>/dev/null || true

    echo "==> 安装 metainfo"
    install -Dm0644 "$PREFIX/data/com.zhongshu.provinces.metainfo.xml" \
        "$METAINFO_DIR/com.zhongshu.provinces.metainfo.xml"

    echo "==> 安装 Nautilus 扩展"
    mkdir -p "$NAUT_EXT_DIR"
    install -m0644 "$PREFIX/nautilus-extension/zhongshu_menu.py" \
        "$NAUT_EXT_DIR/zhongshu_menu.py"

    echo
    echo "安装完成。请重启 Nautilus 使右键菜单生效："
    echo "   nautilus -q"
    echo "应用启动：从应用菜单搜索\"中书省\"，或运行 zhongshu-app"
}

do_uninstall() {
    require_root "$@"
    echo "==> 卸载中书省…"
    rm -rf "$PREFIX_DEST" "$BIN_DEST"
    rm -f "$APP_DIR/com.zhongshu.provinces.desktop"
    rm -f "$METAINFO_DIR/com.zhongshu.provinces.metainfo.xml"
    rm -f "$ICON_DIR/scalable/apps/$APP_ID.png"
    rm -f "$NAUT_EXT_DIR/zhongshu_menu.py"
    gtk-update-icon-cache -f "$ICON_DIR" 2>/dev/null || true
    echo "卸载完成。"
}

case "${1:-install}" in
    --uninstall|uninstall) do_uninstall ;;
    *) do_install ;;
esac
