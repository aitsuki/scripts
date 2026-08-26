# SDK Installer

## Android SDK

### Ubuntu

```shell
bash -c "$(curl -fsSL https://raw.githubusercontent.com/aitsuki/scripts/main/sdk-installer/android-sdk-installer-for-ubuntu.sh)"
```

安装 OpenJDK（默认 25，选择时会提示对应的 Gradle/AGP 要求）、Android SDK 并配置环境变量。

当前脚本安装：

- Android Command-line Tools build `15859902`（下载时校验 SHA-256）
- 最新稳定版 SDK Platform-Tools（由 `sdkmanager` 从官方仓库解析；当前发布说明版本为 37.0.0）
- Android SDK Platform 36
- Android SDK Build-Tools 36.0.0

脚本会运行 `sdkmanager --licenses`。默认逐项显示协议并由用户确认；也可以明确选择自动接受全部协议。已有旧版 Command-line Tools 会在首次运行新版脚本时更新。

## Flutter SDK

### Ubuntu

```shell
bash -c "$(curl -fsSL https://raw.githubusercontent.com/aitsuki/scripts/main/sdk-installer/flutter-sdk-installer-for-ubuntu.sh)"
```

安装/更新 Flutter SDK (脚本会提示输入 Flutter 版本)，当检测到系统未安装 Android SDK 时支持自动安装。
