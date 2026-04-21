#!/bin/bash
# ST重整选股工具 - 启动脚本

# 切换到项目目录
cd "/Volumes/Storage/Kimi Test Project/st_picker_android"

# 清除Python缓存文件（确保代码修改生效）
echo "清除缓存..."
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 启动应用
echo "启动 ST重整选股工具..."
python main.py
