#!/usr/bin/env python3
"""
ST选股工具 Android APK 构建脚本

本脚本帮助构建Android APK文件
需要安装buildozer工具
"""

import os
import sys
import subprocess
import shutil

def check_buildozer():
    """检查是否安装了buildozer"""
    if shutil.which('buildozer'):
        return True
    
    print("❌ 未找到buildozer工具")
    print("\n安装方法:")
    print("  pip install buildozer")
    print("\n注意: 打包APK需要在Linux环境下进行")
    print("  macOS/Windows用户请使用Docker方式")
    return False

def check_docker():
    """检查是否安装了Docker"""
    if shutil.which('docker'):
        return True
    return False

def build_with_local_buildozer():
    """使用本地buildozer构建"""
    print("="*60)
    print("使用本地buildozer构建APK")
    print("="*60)
    
    # 检查是否在Linux系统
    if sys.platform == 'darwin':
        print("❌ macOS不支持本地构建APK")
        print("请使用Docker方式构建")
        return False
    
    print("\n📦 开始构建...")
    print("⚠️ 首次构建需要下载Android SDK/NDK，可能需要30分钟到数小时")
    print("⚠️ 请确保网络连接稳定\n")
    
    try:
        # 构建debug版本APK
        result = subprocess.run(
            ['buildozer', '-v', 'android', 'debug'],
            cwd='.',
            check=True
        )
        
        if result.returncode == 0:
            print("\n✅ 构建成功!")
            print("\nAPK文件位置: ./bin/stpicker-2.0.0-arm64-v8a_armeabi-v7a-debug.apk")
            return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败: {e}")
        return False
    
    return False

def build_with_docker():
    """使用Docker构建（推荐macOS/Windows用户使用）"""
    print("="*60)
    print("使用Docker构建APK（推荐）")
    print("="*60)
    
    if not check_docker():
        print("❌ 未找到Docker")
        print("\n安装方法:")
        print("  macOS: https://docs.docker.com/desktop/install/mac-install/")
        print("  Windows: https://docs.docker.com/desktop/install/windows-install/")
        return False
    
    print("\n📦 Docker方式构建步骤:")
    print("-"*60)
    print("1. 拉取buildozer镜像:")
    print("   docker pull kivy/buildozer")
    print()
    print("2. 运行构建容器:")
    print("   docker run --rm -v $(pwd):/home/user/app kivy/buildozer android debug")
    print()
    print("3. 构建完成后，APK文件在当前目录的bin/文件夹中")
    print("-"*60)
    
    # 询问是否执行
    response = input("\n是否自动执行Docker构建? (y/n): ")
    if response.lower() == 'y':
        try:
            print("\n📦 正在拉取镜像...")
            subprocess.run(['docker', 'pull', 'kivy/buildozer'], check=True)
            
            print("\n📦 开始构建APK（这可能需要很长时间）...")
            result = subprocess.run([
                'docker', 'run', '--rm',
                '-v', f'{os.getcwd()}:/home/user/app',
                'kivy/buildozer',
                'android', 'debug'
            ], check=True)
            
            if result.returncode == 0:
                print("\n✅ 构建成功!")
                print("\nAPK文件位置: ./bin/*.apk")
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"\n❌ 构建失败: {e}")
            return False
    
    return True

def create_github_actions_workflow():
    """创建GitHub Actions工作流文件，用于自动构建APK"""
    workflow_dir = ".github/workflows"
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow_content = '''name: Build Android APK

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install buildozer cython

    - name: Build APK
      run: |
        buildozer android debug

    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: ST选股工具-Android
        path: bin/*.apk
'''
    
    workflow_file = os.path.join(workflow_dir, "build-apk.yml")
    with open(workflow_file, 'w') as f:
        f.write(workflow_content)
    
    print(f"✅ GitHub Actions工作流已创建: {workflow_file}")
    print("\n使用方法:")
    print("1. 将代码推送到GitHub仓库")
    print("2. GitHub Actions会自动构建APK")
    print("3. 在Actions页面下载构建好的APK")

def show_manual_build_instructions():
    """显示手动构建说明"""
    print("="*60)
    print("手动构建APK指南")
    print("="*60)
    
    print("""
方法1: 使用GitHub Actions自动构建（最简单）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 将项目推送到GitHub仓库
2. 已创建的.github/workflows/build-apk.yml会自动触发构建
3. 在GitHub仓库的Actions页面下载APK

方法2: 使用Docker构建（推荐）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 安装Docker
2. 执行以下命令:

   docker pull kivy/buildozer
   docker run --rm -v $(pwd):/home/user/app kivy/buildozer android debug

3. APK文件将生成在 ./bin/ 目录

方法3: 使用Linux虚拟机
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 安装Ubuntu虚拟机
2. 安装依赖:
   
   sudo apt update
   sudo apt install -y python3-pip python3-venv git
   pip3 install --user buildozer cython

3. 构建APK:
   
   cd st_picker_android
   buildozer android debug

方法4: 使用Google Colab
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 上传代码到Google Drive
2. 在Colab中挂载Drive并执行构建
3. 下载生成的APK
""")

def main():
    """主函数"""
    print("="*60)
    print("ST选股工具 - Android APK 构建助手")
    print("="*60)
    print()
    
    # 显示菜单
    print("请选择构建方式:")
    print()
    print("1. 🚀 使用GitHub Actions自动构建（推荐，最简单）")
    print("2. 🐳 使用Docker构建（推荐macOS/Windows用户）")
    print("3. 💻 使用本地buildozer（仅Linux）")
    print("4. 📖 查看详细手动构建指南")
    print("5. ⬇️  下载预编译APK（如果有）")
    print()
    
    choice = input("请输入选项 (1-5): ").strip()
    
    if choice == '1':
        create_github_actions_workflow()
        print("\n✅ GitHub Actions配置完成!")
        print("请将代码推送到GitHub仓库，Actions会自动构建APK")
        
    elif choice == '2':
        build_with_docker()
        
    elif choice == '3':
        if check_buildozer():
            build_with_local_buildozer()
        
    elif choice == '4':
        show_manual_build_instructions()
        
    elif choice == '5':
        print("\n📥 预编译APK下载")
        print("-"*60)
        print("请访问GitHub Releases页面下载最新APK:")
        print("https://github.com/[your-username]/[your-repo]/releases")
        print()
        print("或者联系开发者获取APK文件")
        
    else:
        print("无效选项")

if __name__ == '__main__':
    main()
