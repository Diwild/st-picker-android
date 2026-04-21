#!/bin/bash
# ST选股工具 macOS 本地构建脚本

set -e

echo "=========================================="
echo "ST选股工具 - Android APK 构建脚本 (macOS)"
echo "=========================================="
echo ""

# 设置环境变量
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
export PATH=$JAVA_HOME/bin:$PATH

# 检查依赖
echo "📋 检查依赖..."

if ! command -v buildozer &> /dev/null; then
    echo "❌ buildozer 未安装，正在安装..."
    pip install buildozer cython
fi

if ! command -v java &> /dev/null; then
    echo "❌ Java 未安装，请先安装 OpenJDK 17"
    echo "   brew install openjdk@17"
    exit 1
fi

echo "✅ 依赖检查完成"
echo ""

# 使用无空格路径
BUILD_DIR="$HOME/st_picker_build"
if [ ! -d "$BUILD_DIR" ]; then
    echo "📂 复制项目到无空格路径..."
    cp -R "$(dirname "$0")" "$BUILD_DIR"
fi

cd "$BUILD_DIR"

echo "🚀 开始构建 APK..."
echo "⚠️  首次构建需要 30-60 分钟，请耐心等待"
echo ""

# 开始构建
buildozer android debug

echo ""
echo "=========================================="
if [ -f "bin/stpicker-3.0.0-arm64-v8a_armeabi-v7a-debug.apk" ]; then
    echo "✅ 构建成功！"
    echo ""
    echo "📱 APK 文件位置:"
    echo "   $BUILD_DIR/bin/stpicker-3.0.0-arm64-v8a_armeabi-v7a-debug.apk"
    echo ""
    echo "📲 安装到手机:"
    echo "   adb install -r $BUILD_DIR/bin/stpicker-3.0.0-arm64-v8a_armeabi-v7a-debug.apk"
else
    echo "❌ 构建可能失败，请检查日志"
fi
echo "=========================================="
