#!/usr/bin/env bash

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

echo "正在更新包索引..."
sudo apt update

echo "正在安装所需依赖..."
sudo apt install -y curl wget git unzip xz-utils zip libglu1-mesa

echo "配置 git 凭证为 store"
git config --global credential.helper store

echo "正在安装 $jdk_version..."
sudo apt install -y $jdk_version

# 创建Android SDK目录
ANDROID_HOME="$HOME/Android/Sdk"
echo "正在创建Android SDK目录..."
mkdir -p "$ANDROID_HOME"

# 下载Android命令行工具
echo "正在下载Android命令行工具..."
TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
TEMP_ZIP="/tmp/sdk-tools.zip"
wget -O "$TEMP_ZIP" "$TOOLS_URL"

# 解压命令行工具
echo "正在解压命令行工具..."
mkdir -p "$ANDROID_HOME/cmdline-tools/latest"
unzip -q -d "/tmp/cmdline-tools" "$TEMP_ZIP"
mv /tmp/cmdline-tools/cmdline-tools/* "$ANDROID_HOME/cmdline-tools/latest"
rmdir /tmp/cmdline-tools/cmdline-tools
rmdir /tmp/cmdline-tools
rm "$TEMP_ZIP"

# 设置环境变量
echo "正在设置环境变量..."
cat <<EOF >> "$HOME/.bashrc"

# Android SDK 环境变量
export ANDROID_HOME="\$HOME/Android/Sdk"
export PATH="\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools"
EOF

# 加载环境变量
source "$HOME/.bashrc"

# 接受Android SDK许可
echo "正在安装基本的SDK组件..."
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "platform-tools" "platforms;android-35" "build-tools;35.0.0"

echo "Android SDK 安装完成！"
echo "SDK位置: $ANDROID_HOME"
echo "请运行 'source ~/.bashrc' 或重新启动终端以应用环境变量更改"
