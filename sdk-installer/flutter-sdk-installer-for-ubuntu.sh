#!/usr/bin/env bash

# 获取脚本所在的仓库 URL（为远程执行准备）
REPO_URL="https://raw.githubusercontent.com/aitsuki/scripts/main/sdk-installer"
ANDROID_INSTALLER_URL="${REPO_URL}/android-sdk-installer-for-ubuntu.sh"

echo "======== Flutter SDK 安装程序 ========"

# 检查是否已存在 Flutter 目录
FLUTTER_HOME="$HOME/flutter"
REINSTALL_FLUTTER="n"
if [ -d "$FLUTTER_HOME" ]; then
    echo "检测到已存在 Flutter 目录，是否重新安装？[y/N]"
    read -r REINSTALL_FLUTTER
fi

# 请求输入 Flutter 版本号
echo "请输入要安装的 Flutter 版本号 (例如 3.19.3):"
read -ep "版本: " flutter_version

# 验证版本号输入
if [ -z "$flutter_version" ]; then
    echo "错误: 未输入版本号，安装终止"
    exit 1
fi

echo "======== 开始安装 ========"

# 检查是否已安装 Android SDK
if [ -z "$ANDROID_HOME" ] || [ ! -d "$HOME/Android/Sdk" ]; then
    echo "未检测到 Android SDK，将先安装 Android SDK..."
    
    echo "正在下载 Android SDK 安装脚本..."
    ANDROID_INSTALLER_PATH="/tmp/android-sdk-installer.sh"
    curl -fsSL --connect-timeout 30 "$ANDROID_INSTALLER_URL" -o "$ANDROID_INSTALLER_PATH"
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

echo "正在安装 Flutter SDK 版本 $flutter_version..."

# 安装必要的依赖
echo "正在安装必要的依赖..."
sudo apt update
sudo apt install -y wget curl unzip xz-utils zip libglu1-mesa

# 下载和安装 Flutter SDK
download_flutter() {
    # 构建下载链接
    local download_url="https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${flutter_version}-stable.tar.xz"
    local archive_file="/tmp/flutter.tar.xz"
    
    echo "正在下载 Flutter SDK 版本 $flutter_version..."
    echo "下载链接: $download_url"
    
    # 下载 Flutter SDK 压缩包
    if ! curl -fSL --connect-timeout 60 "$download_url" -o "$archive_file"; then
        echo "下载失败，请检查版本号是否正确或网络连接是否正常"
        return 1
    fi
    
    # 解压 Flutter SDK
    echo "正在解压 Flutter SDK..."
    mkdir -p "$HOME"
    tar xf "$archive_file" -C "$HOME"
    
    # 清理临时文件
    rm -f "$archive_file"
    return 0
}

# 处理 Flutter 安装
if [ -d "$FLUTTER_HOME" ]; then
    if [[ $REINSTALL_FLUTTER =~ ^[Yy]$ ]]; then
        echo "正在删除旧的 Flutter 安装..."
        rm -rf "$FLUTTER_HOME"
        
        # 下载并安装指定版本
        if ! download_flutter; then
            echo "Flutter 安装失败"
            exit 1
        fi
    else
        echo "跳过安装 Flutter SDK"
    fi
else
    # 下载并安装指定版本
    if ! download_flutter; then
        echo "Flutter 安装失败"
        exit 1
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

# 如果 Flutter 目录存在
if [ -d "$FLUTTER_HOME" ]; then
    # 禁用 Flutter 分析
    echo "禁用 Flutter 分析..."
    "$FLUTTER_HOME/bin/flutter" --disable-analytics

    # 检查 Flutter 安装
    echo "正在检查 Flutter 安装..."
    "$FLUTTER_HOME/bin/flutter" doctor

    echo "Flutter 安装完成！"
    echo "Flutter 版本："
    "$FLUTTER_HOME/bin/flutter" --version
fi

echo ""
echo "如需切换版本，请重新运行本脚本并指定所需版本号"
echo ""
echo "现在请运行 'source ~/.bashrc' 或重新启动终端以应用环境变量更改"