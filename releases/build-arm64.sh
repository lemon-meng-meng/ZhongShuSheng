#!/bin/bash
# ARM64 (aarch64) AppImage 构建命令
# 在 ARM64 设备上运行，或使用 QEMU 用户模式模拟交叉构建
#
# 前置条件：
# 1. 安装 appimagetool (ARM64 版本)
# 2. 确保系统已安装 GTK4 + libadwaita + pkexec (运行时依赖)

set -e

echo "=== 构建 ARM64 AppImage ==="
echo "目标架构: aarch64"

# 方法 1: 原生 ARM64 设备上构建
# bash packaging/build-appimage.sh aarch64

# 方法 2: x86_64 上使用 QEMU 用户模式交叉构建 (需要安装 qemu-user-static)
# 注意: 交叉构建 AppImage 较复杂，推荐在目标架构设备上原生构建

# 下载 ARM64 版 appimagetool
# curl -L -o /tmp/appimagetool-aarch64.AppImage \
#   "https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-aarch64.AppImage"
# chmod +x /tmp/appimagetool-aarch64.AppImage
# APPIMAGETOOL=/tmp/appimagetool-aarch64.AppImage bash packaging/build-appimage.sh aarch64

# 方法 3: 使用 Docker 交叉构建 (推荐用于 CI/CD)
# docker run --rm -v $(pwd):/src -w /src multiarch/ubuntu-debootstrap:arm64-noble \
#   bash -c "apt-get update && apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-libadwaita-1 \
#     python3-magic libmagic1 pkexec python3-nautilus nautilus fuse libfuse2 wget && \
#     wget -O /tmp/appimagetool.AppImage https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-aarch64.AppImage && \
#     chmod +x /tmp/appimagetool.AppImage && \
#     APPIMAGETOOL=/tmp/appimagetool.AppImage bash packaging/build-appimage.sh aarch64"

echo ""
echo "构建产物将输出到: releases/zhongshu-aarch64.AppImage"
echo ""
echo "推荐方式: 在 ARM64 设备 (如树莓派 4/5、华为鲲鹏服务器、Mac M 系列通过 UTM 等) 上原生运行："
echo "  bash packaging/build-appimage.sh aarch64"