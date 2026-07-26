# 中书省 · Zhongshu

> 在 Ubuntu / GNOME 桌面上，于「主目录之外」对文件与文件夹进行授权、移动、删除、
> 新建与重命名的图形化小工具；通过 `pkexec` 进行图形化提权，无需记忆任何终端命令。

## 为什么有这个项目

在 home 目录之外执行写操作（如 `mv`、`chmod +x`、`rm -rf`）默认需要 `sudo`，
只能靠命令行完成。这给不太熟悉终端的用户带来很大障碍。

「中书省」取古代决策机构之意，把一切操作封装成 5 个图形化按钮 + 1 个
Nautilus 右键菜单，让任何用户都可以安全、直观地进行这些特权操作。

## 功能

一级界面（应用主窗口）：

1. **授予运行权限** —— 给二进制文件 `chmod +x`（自动检测是否可执行）
2. **移动到** —— 把文件/文件夹移动到任意目录（如 `/opt`）
3. **删除** —— 删除非 home 目录下的文件/文件夹，强制二次确认
4. **新建文件夹** —— 在任意目录下创建文件夹
5. **重命名** —— 在原目录下重命名

二级界面流程：**选择目标 → 行相关操作 → 输入密码 → 完成**。

Nautilus 右键菜单「使用中书省操作」会出现在任意文件/文件夹上，提供完整 5 个二级选项；
在空白处右键，仅提供「新建文件夹」与「新建文件」。

## 技术栈

| 模块 | 选型 |
|------|------|
| GUI 框架 | GTK 4 + Libadwaita |
| 语言 | Python 3 |
| 提权 | pkexec（PolicyKit） |
| 右键菜单 | python3-nautilus 扩展 |
| 打包 | 原生 debian/ 目录 + dpkg-buildpackage · AppImage |

## 依赖

运行时：

```bash
sudo apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-libadwaita-1 \
    python3-magic libmagic1 pkexec python3-nautilus nautilus
```

打包时（可选）：

```bash
sudo apt-get install -y debhelper dh-python devscripts fakeroot \
    desktop-file-utils appstream-util
```

## 项目结构

```
中书省/
├── src/zhongshu/            # Python 源码（包名 zhongshu）
│   ├── __init__.py
│   ├── app.py             # GTK Application 入口
│   ├── window.py          # 主窗口（一级界面）
│   ├── operation_view.py  # 二级操作界面
│   ├── operations.py      # 文件操作工具模块
│   └── runner.py          # 命令执行/参数解析
├── bin/zhongshu-app        # 源码树内启动脚本
├── nautilus-extension/    # Nautilus 右键菜单扩展
├── data/                  # 桌面文件、图标、CSS、metainfo
├── debian/                # 原生 Debian 打包目录
├── packaging/             # deb / AppImage 打包脚本
├── tests/                 # 测试
├── install.sh             # 一键安装到本地系统
└── dist/                  # 构建产物输出目录（gitignore）
```

## 安装

### 选项 A：从源码安装（一处运行）

```bash
sudo bash install.sh
```

卸载：

```bash
sudo bash install.sh --uninstall
```

### 选项 B：安装 .deb 包

```bash
sudo apt-get install -y ./dist/zhongshu_0.1.0-1_all.deb
```

### 选项 C：运行 AppImage

```bash
chmod +x 中书省-x86_64.AppImage
./中书省-x86_64.AppImage
```

> AppImage 仍需系统已安装 GTK4 + libadwaita + pkexec。

## 开发与打包

源码调试：

```bash
PYTHONPATH=src python3 -m zhongshu.app
# 或：
PYTHONPATH=src python3 bin/zhongshu-app
```

构建 deb：

```bash
bash packaging/build-deb.sh
```

构建 AppImage：

```bash
# 1) 一次性准备 appimagetool
wget -O /tmp/appimagetool.AppImage \
    https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x /tmp/appimagetool.AppImage
# Zorin/Ubuntu 22.04+ 需要 libfuse2:
sudo apt-get install -y libfuse2

# 2) 构建
bash packaging/build-appimage.sh
```

## 安全性

- 所有面向用户的写操作前都会进行路径校验（`os.path.abspath`、根目录拒绝等）。
- 删除操作（`rm -rf`）在 GUI 中强制要求勾选二次确认条；
  在 Nautilus 右键菜单中，会显示徽标强调「系统目录」风险提示。
- 所有特权命令严格使用位置参数构造，通过 `--` 终止选项，避免路径名注入。
- 二进制判断使用 libmagic 而非后缀名，避免误授权。

## License

GPL-3.0-or-later，详见 [debian/copyright](debian/copyright)。
