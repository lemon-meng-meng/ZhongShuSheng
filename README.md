# 写在前面的话

1.中国不能产生男女对立，我们承认当且仍有一些忽略女性合理权益的现象，女生为了维护合法权益的勇气和决心值得被肯定被看到。然而极端女权企图把“维护合法权益”和“为了争夺过渡权力以及只享受权利不承担义务”混为一谈。我们必须客观看待女性维权，当前的国际形势不允许我们因为男女对立而更加分裂

2.当前国内有相当多的间谍，若不加以遏制，在战争到来时，这些间谍将是外国的马前卒。历史已经证明了日本人这种生物在直面敌人之前通常已经把敌人渗透的千疮百孔了，若是高市早苗不怕中国，那么就该反思她是不是不一定想在正面战场上和中国硬碰硬了

3.请理性爱国，当前在相当多的邻域我们与世界先进水平依然有差距。医疗、高端工业母机、高性能商用航天发动机以及无数看不见的邻域，有相当多类似蔡司这样外企把握我国产业命脉。尽管这是全球化的必然结果，但不可否认有能力保持独立自主是参与全球化的底牌和有力筹码

4.请认真对待爱情，爱情是藏在人DNA里的特殊基因片段，请不要将爱情理解为“好聚好散”。它不应该被冠上“快餐式”的前缀

5.既需一定的文化自信和“文化自负”。我们决对不是排斥外国文化，但请有意识地告诉自己：若有一天开战，这种文化是可以通过入侵手段作为比热武器更为危险的工具的。更不能因接受他国文化而全盘自我文化。另一方面，我国的文化输出能力尚弱，欧美人对东亚人的知名度大多是：日本人 > 韩国人 > 中国人。很大原因在于日韩的文化输出能力极强。其中不妨国内文娱产业出海动力弱，质量低；而《哪吒·魔童降世》和《哪吒·魔童闹海》则是另一方面的的问题，我不否认其为中华文化传播作出重大贡献，但从文化输出角度来讲，这并不适合推广中华文化传播，因为这需要一定的中国文化基础，简单说就是理解其中的内涵有门槛。因此，希望国内公司更进一步。

# 中书省 · Zhongshu

> 在 Ubuntu / GNOME 桌面上，于「主目录之外」对文件与文件夹进行授权、移动、删除、
> 新建与重命名的图形化小工具；通过 `pkexec` 进行图形化提权，无需记忆任何终端命令。

## 为什么有这个项目

在 home 目录之外执行写操作（如 `mv`、`chmod +x`、`rm -rf`）默认需要 `sudo`，
只能靠命令行完成。这给不太熟悉终端的用户带来很大障碍。

「中书省」取古代决策机构之意，负责草拟皇帝诏令，该工具把一切操作封装成 5 个图形化按钮 + 1 个
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

界面底部提供**语言切换**（中文/English）与**字体粗细切换**（常规/加粗）按钮。

## 技术栈

| 模块     | 选型                                           |
| ------ | -------------------------------------------- |
| GUI 框架 | GTK 4 + Libadwaita                           |
| 语言     | Python 3                                     |
| 提权     | pkexec（PolicyKit）                            |
| 右键菜单   | python3-nautilus 扩展                          |
| 打包     | 原生 debian/ 目录 + dpkg-buildpackage · AppImage |

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
│   ├── runner.py          # 命令执行/参数解析
│   └── i18n.py            # 国际化模块
├── bin/zhongshu-app        # 源码树内启动脚本
├── nautilus-extension/    # Nautilus 右键菜单扩展
├── data/                  # 桌面文件、图标、CSS、metainfo、字体
├── debian/                # 原生 Debian 打包目录
├── packaging/             # deb / AppImage 打包脚本
├── locale/                # 翻译文件
├── tests/                 # 测试
├── install.sh             # 一键安装到本地系统
└── releases/              # 构建产物输出目录（gitignore）
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

### 选项 B：安装 .deb 包（右键菜单随包自动安装）

```bash
sudo apt-get install -y ./releases/zhongshu_0.1.1-1_all.deb
```

deb 安装后无须额外步骤：Nautilus 扩展与启动器随之进入
`/usr/share/nautilus-python/extensions/` 与 `/usr/bin/zhongshu-app`，
postinst 重启 Nautilus 后即可看到右键菜单「使用中书省操作」。

### 选项 C：运行 AppImage（需先部署右键菜单）

```bash
chmod +x releases/zhongshu-x86_64.AppImage
./releases/zhongshu-x86_64.AppImage                  # 启动一级界面
./releases/zhongshu-x86_64.AppImage --install-context-menu   # 部署右键菜单到当前用户
```

执行 `--install-context-menu` 后会自动：

- 在 `~/.local/bin/zhongshu-app` 写入启动器（固定指向当前 AppImage 路径）；
- 把 Nautilus 扩展复制到 `~/.local/share/nautilus-python/extensions/`；
- 重启 Nautilus，使右键菜单立即生效。

卸载右键菜单：

```bash
./releases/zhongshu-x86_64.AppImage --uninstall-context-menu
```

> AppImage 仍需系统已安装 GTK4 + libadwaita + pkexec。

## 多架构支持

本项目支持以下架构：

| 架构 | AppImage | Debian 包 |
|------|----------|-----------|
| x86_64 | ✅ | ✅ |
| aarch64 (ARM64) | ✅ | ✅ |
| loongarch64 | ✅ | ✅ |

构建指定架构的 AppImage：
```bash
bash packaging/build-appimage.sh aarch64
bash packaging/build-appimage.sh loongarch64
```

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
# 1) 一次性准备 appimagetool（具体文件名带版本号前缀，请到
#    https://github.com/probonopd/go-appimage/releases 找最新 continuous 版）
curl -L -o /tmp/appimagetool.AppImage \
    https://github.com/probonopd/go-appimage/releases/download/continuous/appimagetool-x86_64.AppImage
# 若上面 404（continuous 资产重命名为 appimagetool-947-x86_64.AppImage 之类），
# 请在 https://github.com/probonopd/go-appimage/releases 找 glob "appimagetool-*-x86_64.AppImage" 下载
chmod +x /tmp/appimagetool.AppImage

# 2) 构建
bash packaging/build-appimage.sh
```

## 安全性

- 所有面向用户的写操作前都会进行路径校验（`os.path.abspath`、根目录拒绝等）。
- 删除操作（`rm -rf`）在 GUI 中强制要求勾选二次确认条；
  在 Nautilus 右键菜单中，会显示徽标强调「系统目录」风险提示。
- 所有特权命令严格使用位置参数构造，通过 `--` 终止选项，避免路径名注入。
- 二进制判断使用 libmagic 而非后缀名，避免误授权。

## 字体许可证声明

本项目使用 **HarmonyOS Sans** 字体家族，包含以下字体文件：

- `data/fonts/HarmonyOS_Sans_Regular.ttf`（英文常规）
- `data/fonts/HarmonyOS_Sans_Bold.ttf`（英文加粗）
- `data/fonts/HarmonyOS_Sans_SC_Regular.ttf`（中文常规）
- `data/fonts/HarmonyOS_Sans_SC_Bold.ttf`（中文加粗）

**版权归属**：华为设备有限公司 (Huawei Device Co., Ltd.)  
**许可证**：HarmonyOS Sans Fonts License Agreement

主要许可条款摘要：
1. 可免费用于任何软件（除字体软件外）的嵌入、打包、再分发和销售
2. 不得修改字体文件
3. 不得单独分发或销售字体文件
4. 必须在软件中显著位置声明使用了 HarmonyOS Sans 字体
5. 必须保留版权声明和许可证文本

完整许可证文本见 `data/fonts/HarmonyOS_Sans_LICENSE.txt` 与 `data/fonts/HarmonyOS_Sans_SC_LICENSE.txt`。

# 关于图标
本工具的图标由通义万相生成
