#!/bin/bash
# LoongArch64 (loongarch64) AppImage 构建命令
# 在 LoongArch64 设备上运行 (如龙芯 3A5000/3C5000 服务器/台式机)
#
# 前置条件：
# 1. 安装 appimagetool (LoongArch64 版本)
# 2. 确保系统已安装 GTK4 + libadwaita + pkexec (运行时依赖)
# 3. 当前主流 LoongArch 发行版: Loongnix, UOS, 统信 UOS, deepin (LoongArch 版), Arch Linux LoongArch 等

set -e

echo "=== 构建 LoongArch64 AppImage ==="
echo "目标架构: loongarch64"

# 方法 1: 原生 LoongArch64 设备上构建 (推荐)
# bash packaging/build-appimage.sh loongarch64

# 方法 2: 下载 LoongArch64 版 appimagetool (需从 probonopd/go-appimage releases 获取对应版本)
# curl -L -o /tmp/appimagetool-loongarch64.AppImage \
#   "https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-loongarch64.AppImage"
# chmod +x /tmp/appimagetool-loongarch64.AppImage
# APPIMAGETOOL=/tmp/appimagetool-loongarch64.AppImage bash packaging/build-appimage.sh loongarch64

# 方法 3: 使用 Docker 交叉构建 (如果有 loongarch64 镜像)
# docker run --rm -v $(pwd):/src -w /src loongnix/loongnix:latest \
#   bash -c "apt-get update && apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-libadwaita-1 \
#     python3-magic libmagic1 pkexec python3-nautilus nautilus fuse libfuse2 wget && \
#     wget -O /tmp/appimagetool.AppImage https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-loongarch64.AppImage && \
#     chmod +x /tmp/appimagetool.AppImage && \
#     APPIMAGETOOL=/tmp/appimagetool.AppImage bash packaging/build-appimage.sh loongarch64"

echo ""
echo "构建产物将输出到: releases/zhongshu-loongarch64.AppImage"
echo ""
echo "推荐方式: 在 LoongArch64 设备 (龙芯 3A5000/3C5000 等) 上原生运行："
echo "  bash packaging/build-appimage.sh loongarch64"
echo ""
echo "注意: LoongArch 版本的 appimagetool 可能需要从 probonopd/go-appimage 的"
echo "  continuous 构建中获取，文件名类似 appimagetool-*-loongarch64.AppImage"