# FVM Installer

用于在 Windows 上安装 [FVM](https://fvm.app/) 的 PowerShell 脚本。脚本会自动识别 x64 或 ARM64 架构，从 GitHub Releases 下载对应版本，并将安装目录添加到当前用户的 `PATH`。

## 环境要求

- Windows 64 位（x64 或 ARM64）
- PowerShell 5.1 或更高版本
- 能够访问 GitHub API 和 Releases

## 快速安装

在 PowerShell 中执行：

```powershell
irm https://raw.githubusercontent.com/aitsuki/scripts/main/fvm/install-fvm.ps1 | iex
```

默认安装最新版本到 `%LOCALAPPDATA%\fvm`，无需管理员权限。安装完成后可执行以下命令验证：

```powershell
fvm --version
```

## 本地使用

```powershell
.\install-fvm.ps1
```

支持以下参数：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `-Version` | 要安装的 FVM Release 标签，也可使用 `latest` | `latest` |
| `-InstallDir` | 安装目录 | `%LOCALAPPDATA%\fvm` |
| `-Force` | 即使指定版本已安装，也重新下载并安装 | 否 |

示例：

```powershell
# 安装指定版本
.\install-fvm.ps1 -Version "4.3.0"

# 安装到自定义目录
.\install-fvm.ps1 -InstallDir "D:\Tools\fvm"

# 强制重新安装最新版本
.\install-fvm.ps1 -Force
```

脚本会将安装目录写入当前用户的 `PATH`，并立即更新当前 PowerShell 会话。若其他已打开的终端无法识别 `fvm`，请重新打开终端。
