#!/usr/bin/env bash

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
echo "1. OpenJDK 21 (默认)"
echo "2. OpenJDK 17"
echo "3. OpenJDK 11"
read -ep "请输入选项 [1-3]: " jdk_option

jdk_option=${jdk_option:-1}

case $jdk_option in
    1)
        jdk_version="openjdk-21-jdk"
        ;;
    2)
        jdk_version="openjdk-17-jdk"
        ;;
    3)
        jdk_version="openjdk-11-jdk"
        ;;
    *)
        echo "无效的选项，请重新运行脚本。"
        exit 1
        ;;
esac

# 检查JDK是否已安装
if dpkg -l | grep -q "$jdk_version"; then
    echo "$jdk_version 已经安装，跳过安装步骤"
else
    echo "正在更新包索引..."
    sudo apt update

    echo "正在安装所需依赖..."
    sudo apt install -y wget git unzip

    echo "正在安装 $jdk_version..."
    sudo apt install -y $jdk_version
fi

echo "配置 git 凭证为 store"
git config --global credential.helper store

# 创建Android SDK目录
echo "正在创建Android SDK目录..."
mkdir -p "$ANDROID_HOME"

# 检查命令行工具是否已安装
if [ ! -d "$ANDROID_HOME/cmdline-tools/latest" ]; then
    # 下载Android命令行工具
    echo "正在下载Android命令行工具..."
    TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
    TEMP_ZIP="/tmp/sdk-tools.zip"
    wget -O "$TEMP_ZIP" "$TOOLS_URL"

    # 解压命令行工具
    echo "正在解压命令行工具..."
    rm -rf "/tmp/cmdline-tools"
    mkdir -p "$ANDROID_HOME/cmdline-tools/latest"
    unzip -q -d "/tmp/cmdline-tools" "$TEMP_ZIP"
    mv /tmp/cmdline-tools/cmdline-tools/* "$ANDROID_HOME/cmdline-tools/latest"
    rmdir /tmp/cmdline-tools/cmdline-tools
    rmdir /tmp/cmdline-tools
    rm "$TEMP_ZIP"
else
    echo "Android命令行工具已安装，跳过下载和解压步骤"
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

# 接受Android SDK许可并安装组件
echo "正在安装基本的SDK组件..."
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platform-tools" "platforms;android-35" "build-tools;35.0.0"

echo "Android SDK 安装完成！"
echo "SDK位置: $ANDROID_HOME"
echo "请运行 'source ~/.bashrc' 或重新启动终端以应用环境变量更改"
