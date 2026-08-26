#!/usr/bin/env bash

set -e

# 版本配置（更新时请同时更新下载地址和 SHA-256）
CMDLINE_TOOLS_BUILD="15859902"
CMDLINE_TOOLS_SHA256="4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583"
ANDROID_PLATFORM="36"
ANDROID_BUILD_TOOLS="36.0.0"

# 检查是否已经安装Android SDK
ANDROID_HOME="$HOME/Android/Sdk"
if [ -d "$ANDROID_HOME/cmdline-tools/latest" ] && [ -d "$ANDROID_HOME/platform-tools" ]; then
    echo "检测到Android SDK已安装在 $ANDROID_HOME"
    read -ep "是否继续安装? (y/N): " continue_install
    if [[ ! "$continue_install" =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 0
    fi
    echo "将继续安装过程..."
fi

echo "请选择JDK版本:"
echo "1. OpenJDK 25 (默认；运行 Gradle 需 9.1+，适合 AGP 9.x 新项目)"
echo "2. OpenJDK 21 (运行 Gradle 需 8.5+，适合较新的 AGP 8.x/9.x 项目)"
echo "3. OpenJDK 17 (运行 Gradle 需 7.3+；AGP 8.x/9.x 的最低 JDK)"
echo "注：新版 Android Command-line Tools 要求 JDK 17+；AGP 7.x 等旧项目请另行配置 JDK 11。"
read -ep "请输入选项 [1-3]: " jdk_option

jdk_option=${jdk_option:-1}

case $jdk_option in
    1) jdk_package="openjdk-25-jdk" ;;
    2) jdk_package="openjdk-21-jdk" ;;
    3) jdk_package="openjdk-17-jdk" ;;
    *)
        echo "无效的选项，请重新运行脚本。"
        exit 1
        ;;
esac

# 安装依赖和所选 JDK
if dpkg-query -W -f='${Status}' "$jdk_package" 2>/dev/null | grep -q "install ok installed"; then
    echo "$jdk_package 已经安装，跳过 JDK 安装步骤"
    sudo apt install -y wget git unzip
else
    echo "正在更新包索引..."
    sudo apt update

    echo "正在安装所需依赖和 $jdk_package..."
    if ! sudo apt install -y wget git unzip "$jdk_package"; then
        echo "无法安装 $jdk_package。请确认当前 Ubuntu 版本的软件源提供该版本，或改选其他 JDK。" >&2
        exit 1
    fi
fi

echo "配置 git 凭证为 store"
git config --global credential.helper store

# 创建Android SDK目录
echo "正在创建Android SDK目录..."
mkdir -p "$ANDROID_HOME"

# 安装或更新 Android 命令行工具
CMDLINE_TOOLS_DIR="$ANDROID_HOME/cmdline-tools/latest"
CMDLINE_TOOLS_MARKER="$CMDLINE_TOOLS_DIR/.installer-build"
installed_tools_build=""
if [ -f "$CMDLINE_TOOLS_MARKER" ]; then
    installed_tools_build=$(<"$CMDLINE_TOOLS_MARKER")
fi

if [ "$installed_tools_build" != "$CMDLINE_TOOLS_BUILD" ]; then
    echo "正在下载 Android 命令行工具（build $CMDLINE_TOOLS_BUILD）..."
    TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_BUILD}_latest.zip"
    TEMP_DIR=$(mktemp -d)
    TEMP_ZIP="$TEMP_DIR/commandline-tools.zip"
    trap 'rm -rf "$TEMP_DIR"' EXIT
    wget -O "$TEMP_ZIP" "$TOOLS_URL"

    echo "正在校验并解压 Android 命令行工具..."
    echo "$CMDLINE_TOOLS_SHA256  $TEMP_ZIP" | sha256sum --check --status || {
        echo "Android 命令行工具校验失败，已停止安装。" >&2
        exit 1
    }
    unzip -q -d "$TEMP_DIR/unpacked" "$TEMP_ZIP"
    rm -rf "$CMDLINE_TOOLS_DIR"
    mkdir -p "$CMDLINE_TOOLS_DIR"
    mv "$TEMP_DIR/unpacked/cmdline-tools/"* "$CMDLINE_TOOLS_DIR/"
    echo "$CMDLINE_TOOLS_BUILD" > "$CMDLINE_TOOLS_MARKER"
    rm -rf "$TEMP_DIR"
    trap - EXIT
else
    echo "Android 命令行工具 build $CMDLINE_TOOLS_BUILD 已安装，跳过下载"
fi

# 检查环境变量是否已设置
if ! grep -q "# Android SDK 环境变量" "$HOME/.bashrc"; then
    # 设置环境变量
    echo "正在设置环境变量..."
    cat <<EOF >> "$HOME/.bashrc"

# Android SDK 环境变量
export ANDROID_HOME="\$HOME/Android/Sdk"
export PATH="\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools"
EOF
else
    echo "环境变量已设置，跳过"
fi

# 加载环境变量（确保后续命令可用）
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"

# 接受 Android SDK 许可并安装组件
SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
echo "安装 SDK 组件前需要接受 Google/Android 的许可协议。"
read -ep "是否自动对所有许可协议回答 y？请确保你已阅读并同意这些协议 (y/N): " auto_accept_licenses
if [[ "$auto_accept_licenses" =~ ^[Yy]$ ]]; then
    yes | "$SDKMANAGER" --licenses
else
    echo "将逐项显示许可协议，请阅读后输入 y 或 N："
    "$SDKMANAGER" --licenses
fi

# platform-tools 不带版本号；sdkmanager 会安装/更新到仓库中的最新稳定版。
echo "正在安装/更新 SDK Platform-Tools、Android $ANDROID_PLATFORM 平台和 Build-Tools $ANDROID_BUILD_TOOLS..."
"$SDKMANAGER" --install \
    "platform-tools" \
    "platforms;android-$ANDROID_PLATFORM" \
    "build-tools;$ANDROID_BUILD_TOOLS"

echo "Android SDK 安装完成！"
echo "SDK位置: $ANDROID_HOME"
echo "请运行 'source ~/.bashrc' 或重新启动终端以应用环境变量更改"
