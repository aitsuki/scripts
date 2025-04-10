#!/usr/bin/env sh

# 获取脚本所在的仓库 URL（为远程执行准备）
REPO_URL="https://raw.githubusercontent.com/aitsuki/script/main/sdk-installer"
ANDROID_INSTALLER_URL="${REPO_URL}/android-sdk-installer-for-ubuntu.sh"

echo "======== Flutter SDK 安装程序 ========"

# 检查是否已存在 Flutter 目录
FLUTTER_HOME="$HOME/flutter"
REINSTALL_FLUTTER="n"
if [ -d "$FLUTTER_HOME" ]; then
    echo "检测到已存在 Flutter 目录，是否重新安装？[y/N]"
    read -r REINSTALL_FLUTTER
fi

# 提供 Flutter 版本选择
echo "请选择要安装的 Flutter 版本:"
echo "1. 最新稳定版 (stable channel) [默认]"
echo "2. 指定具体版本 (例如 3.13.9)"
read -ep "请输入选项 [1-2]: " flutter_option

flutter_option=${flutter_option:-1}
flutter_channel="stable"
flutter_version=""

case $flutter_option in
    1)
        flutter_channel="stable"
        flutter_version=""
        ;;
    2)
        flutter_channel=""
        echo "请输入具体的 Flutter 版本号 (例如 3.13.9):"
        read -ep "版本: " flutter_version
        if [ -z "$flutter_version" ]; then
            echo "未输入版本号，将使用最新稳定版"
            flutter_channel="stable"
            flutter_version=""
        fi
        ;;
    *)
        echo "无效选项，将使用最新稳定版"
        flutter_channel="stable"
        flutter_version=""
        ;;
esac

echo "======== 开始安装 ========"

# 检查是否已安装 Android SDK
if [ -z "$ANDROID_HOME" ] || [ ! -d "$HOME/Android/Sdk" ]; then
    echo "未检测到 Android SDK，将先安装 Android SDK..."
    
    echo "正在下载 Android SDK 安装脚本..."
    ANDROID_INSTALLER_PATH="/tmp/android-sdk-installer.sh"
    curl -fsSL "$ANDROID_INSTALLER_URL" -o "$ANDROID_INSTALLER_PATH"
    chmod +x "$ANDROID_INSTALLER_PATH"
    
    echo "正在执行 Android SDK 安装脚本..."
    bash "$ANDROID_INSTALLER_PATH"
    
    # 清理临时文件
    rm "$ANDROID_INSTALLER_PATH"
    
    # 重新加载环境变量
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc"
    fi

    # 确保 ANDROID_HOME 已经设置
    if [ -z "$ANDROID_HOME" ]; then
        export ANDROID_HOME="$HOME/Android/Sdk"
    fi
fi

echo "正在安装 Flutter SDK..."

# 安装必要的依赖
echo "正在安装必要的依赖..."
sudo apt update
sudo apt install -y wget curl git unzip xz-utils zip libglu1-mesa

# 处理 Flutter 安装
if [ -d "$FLUTTER_HOME" ]; then
    if [[ $REINSTALL_FLUTTER =~ ^[Yy]$ ]]; then
        echo "正在删除旧的 Flutter 安装..."
        rm -rf "$FLUTTER_HOME"
        
        # 根据选择下载对应的 Flutter 版本
        if [ -n "$flutter_version" ]; then
            echo "正在下载 Flutter SDK 版本 $flutter_version..."
            git clone https://github.com/flutter/flutter.git "$FLUTTER_HOME"
            cd "$FLUTTER_HOME"
            git fetch --tags
            git checkout tags/$flutter_version
        else
            echo "正在下载 Flutter SDK ($flutter_channel channel)..."
            git clone https://github.com/flutter/flutter.git -b $flutter_channel "$FLUTTER_HOME"
        fi
    else
        echo "跳过安装 Flutter SDK"
    fi
else
    # 根据选择下载对应的 Flutter 版本
    if [ -n "$flutter_version" ]; then
        echo "正在下载 Flutter SDK 版本 $flutter_version..."
        git clone https://github.com/flutter/flutter.git "$FLUTTER_HOME"
        cd "$FLUTTER_HOME"
        git fetch --tags
        git checkout tags/$flutter_version
    else
        echo "正在下载 Flutter SDK ($flutter_channel channel)..."
        git clone https://github.com/flutter/flutter.git -b $flutter_channel "$FLUTTER_HOME"
    fi
fi

# 设置环境变量
echo "正在设置 Flutter 环境变量..."
if ! grep -q "FLUTTER_HOME" "$HOME/.bashrc"; then
    cat <<EOF >> "$HOME/.bashrc"

# Flutter 环境变量
export FLUTTER_HOME="\$HOME/flutter"
export PATH="\$PATH:\$FLUTTER_HOME/bin"
EOF
fi

# 临时设置 PATH 环境变量
export PATH="$PATH:$FLUTTER_HOME/bin"

# 预下载 Flutter 依赖
echo "正在预下载 Flutter 依赖..."
"$FLUTTER_HOME/bin/flutter" precache

# 检查 Flutter 安装
echo "正在检查 Flutter 安装..."
"$FLUTTER_HOME/bin/flutter" doctor

# 禁用 Flutter 分析
echo "禁用 flutter 分析"
"$FLUTTER_HOME/bin/flutter" --disable-analytics

echo "Flutter 安装完成！"
echo "Flutter 版本："
"$FLUTTER_HOME/bin/flutter" --version

echo ""
echo "======== Flutter 版本管理提示 ========"
echo "你随时可以使用 Git 命令切换 Flutter 版本："
echo ""
echo "1. 切换到稳定版:"
echo "   cd $FLUTTER_HOME && git checkout stable"
echo ""
echo "2. 切换到特定版本(例如 3.13.9):"
echo "   cd $FLUTTER_HOME && git fetch --tags && git checkout tags/3.13.9"
echo ""
echo "切换版本后，建议运行:"
echo "   flutter doctor"
echo "   flutter precache"
echo "确保环境设置正确"

echo "现在请运行 'source ~/.bashrc' 或重新启动终端以应用环境变量更改"