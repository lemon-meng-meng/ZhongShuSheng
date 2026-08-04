#!/usr/bin/env bash
# packaging/build-deb.sh —— 在源码目录下构建 zhongshu_0.1.0-1_all.deb
#
# 用法：
#   bash packaging/build-deb.sh
#
# 需要：debhelper, dh-python, devscripts, dpkg-dev
# 输出 dist/zhongshu_0.1.0-1_all.deb

set -e

HERE="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$HERE/dist"
mkdir -p "$DIST"

echo "==> 进入项目目录 $HERE"
cd "$HERE"

echo "==> 提供源码包元数据"
# native 包：直接对当前目录构建，不需要 orig tar。
# 但是 dpkg-buildpackage 会要求 source，我们用 --no-sign --build=binary 跳过。

echo "==> 执行 dpkg-buildpackage"
DEB_BUILD_OPTIONS="nocheck" dpkg-buildpackage -us -uc -b 2>&1 || {
    echo "dpkg-buildpackage 失败。若缺少依赖："
    echo "  sudo apt-get install -y debhelper dh-python devscripts fakeroot"
    exit 1
}

echo "==> 收集构建产物到 $DIST"
shopt -s nullglob
for f in "${HERE}/.."/*.deb "${HERE}/.."/*.buildinfo "${HERE}/.."/*.changes; do
    mv -f "$f" "$DIST/"
done

echo
echo "完成 → $DIST"
ls -la "$DIST"
