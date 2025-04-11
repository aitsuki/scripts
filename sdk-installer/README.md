# SDK Installer

## Android SDK

### Ubuntu

```shell
bash -c "$(curl -fsSL https://raw.githubusercontent.com/aitsuki/scripts/main/sdk-installer/android-sdk-installer-for-ubuntu.sh)"
```

安装 OpenJDK (脚本会提示选择JDK版本)，Android SDK 并配置环境变量。

## Flutter SDK

### Ubuntu

```shell
bash -c "$(curl -fsSL https://raw.githubusercontent.com/aitsuki/scripts/main/sdk-installer/flutter-sdk-installer-for-ubuntu.sh)"
```

安装 Flutter SDK (脚本会提示输入Flutter版本)，当检测到系统未安装 Android SDK 时支持自动安装。
