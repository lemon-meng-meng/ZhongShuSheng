#!/bin/bash

# 安装依赖
sudo apt install -y python3-gi python3-magic gir1.2-gtk-4.0 gir1.2-adw-1 \
    python3-nautilus

# 复制应用文件
sudo mkdir -p /opt/zhongshu-provinces
sudo cp -r src/* /opt/zhongshu-provinces/
sudo cp data/style.css /opt/zhongshu-provinces/

# 创建启动器
sudo tee /usr/local/bin/zhongshu-app << 'EOF'#!/bin/bashcd /opt/zhongshu-provincespython3 main.py "$@"EOF
sudo chmod +x /usr/local/bin/zhongshu-app

# 安装Nautilus扩展
mkdir -p ~/.local/share/nautilus-python/extensions
cp nautilus-extension/zhongshu-menu.py ~/.local/share/nautilus-python/extensions/

# 创建.desktop文件
sudo tee /usr/share/applications/com.example.zhongshu.desktop << EOF[Desktop Entry]Name=中书省Comment=系统目录文件管理工具Exec=zhongshu-appIcon=system-file-managerType=ApplicationCategories=System;FileTools;EOF

echo "安装完成！请重启Nautilus: nautilus -q"