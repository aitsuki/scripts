# JADX Installer

用于在 Windows 上安装 [JADX](https://github.com/skylot/jadx) 的 PowerShell 脚本。

脚本下载官方完整发行包 `jadx-<version>.zip`，同时安装以下组件，而不是只安装 GUI 版本：

- `jadx`：命令行反编译工具
- `jadx-gui`：图形界面反编译工具

## 环境要求

- Windows
- PowerShell 5.1 或更高版本
- 64 位 Java 11 或更高版本
- 能够访问 GitHub API 和 Releases

## 快速安装

在 PowerShell 中执行：

```powershell
irm https://raw.githubusercontent.com/aitsuki/scripts/main/jadx/install-jadx.ps1 | iex
```

默认安装最新版本到 `%LOCALAPPDATA%\jadx`，并将 `%LOCALAPPDATA%\jadx\bin` 添加到当前用户的 `PATH`，无需管理员权限。

安装完成后可分别验证命令行和 GUI：

```powershell
jadx --version
jadx-gui
```

## 本地使用

```powershell
.\install-jadx.ps1
```

支持以下参数：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `-Version` | Release 版本或标签，例如 `1.5.3`、`v1.5.3`，也可使用 `latest` | `latest` |
| `-InstallDir` | 安装目录 | `%LOCALAPPDATA%\jadx` |
| `-Force` | 即使指定版本已安装，也重新下载并安装 | 否 |

示例：

```powershell
# 安装指定版本
.\install-jadx.ps1 -Version "1.5.3"

# 安装到自定义目录
.\install-jadx.ps1 -InstallDir "D:\Tools\jadx"

# 强制重新安装最新版本
.\install-jadx.ps1 -Force
```

若安装后其他已打开的终端无法识别 `jadx` 或 `jadx-gui`，请重新打开终端。
