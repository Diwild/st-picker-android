#!/bin/bash
#
# ST Picker Android 版 - 定时任务配置脚本
# 一键配置 macOS/Linux cron 定时自动更新
#

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AUTO_UPDATE_SCRIPT="${PROJECT_DIR}/scripts/auto_update.sh"
LOG_DIR="${PROJECT_DIR}/logs"

# 确保脚本可执行
chmod +x "$AUTO_UPDATE_SCRIPT"
mkdir -p "$LOG_DIR"

echo "========================================"
echo "  ST Picker Android 定时任务配置"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "更新脚本: $AUTO_UPDATE_SCRIPT"
echo "日志目录: $LOG_DIR"
echo ""

# 检查当前 crontab
echo "当前定时任务:"
crontab -l 2>/dev/null | grep -i "st-picker\|st_picker_build" || echo "  （无 ST Picker 相关任务）"
echo ""

echo "可选定时方案："
echo "  [1] 每天收盘后运行一次（15:30，工作日）"
echo "  [2] 每天运行两次（11:30 和 15:30，工作日）"
echo "  [3] 每天运行三次（09:30、11:30、15:30，工作日）"
echo "  [4] 自定义"
echo "  [0] 删除现有 ST Picker 定时任务"
echo ""

read -p "请选择 (0-4，默认 1): " CHOICE
CHOICE=${CHOICE:-1}

# 先删除旧的 ST Picker 任务
crontab -l 2>/dev/null | grep -v "st_picker_build.*auto_update" > /tmp/cron_tmp.txt || true

case "$CHOICE" in
    1)
        # 每天 15:30，工作日
        echo "PATH=/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin" >> /tmp/cron_tmp.txt
        echo "30 15 * * 1-5 cd ${PROJECT_DIR} && ./scripts/auto_update.sh >> ${LOG_DIR}/cron.log 2>&1" >> /tmp/cron_tmp.txt
        echo "✅ 已配置: 每天 15:30（工作日）自动更新"
        ;;
    2)
        # 每天 11:30 和 15:30，工作日
        echo "PATH=/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin" >> /tmp/cron_tmp.txt
        echo "30 11,15 * * 1-5 cd ${PROJECT_DIR} && ./scripts/auto_update.sh >> ${LOG_DIR}/cron.log 2>&1" >> /tmp/cron_tmp.txt
        echo "✅ 已配置: 每天 11:30 和 15:30（工作日）自动更新"
        ;;
    3)
        # 每天 09:30、11:30、15:30，工作日
        echo "PATH=/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin" >> /tmp/cron_tmp.txt
        echo "30 9,11,15 * * 1-5 cd ${PROJECT_DIR} && ./scripts/auto_update.sh >> ${LOG_DIR}/cron.log 2>&1" >> /tmp/cron_tmp.txt
        echo "✅ 已配置: 每天 09:30、11:30、15:30（工作日）自动更新"
        ;;
    4)
        echo ""
        echo "请输入自定义 cron 表达式（例如：30 15 * * 1-5）"
        echo "格式: 分钟 小时 日期 月份 星期"
        read -p "Cron 表达式: " CUSTOM_CRON
        if [ -z "$CUSTOM_CRON" ]; then
            echo "❌ 表达式不能为空"
            exit 1
        fi
        echo "PATH=/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin" >> /tmp/cron_tmp.txt
        echo "${CUSTOM_CRON} cd ${PROJECT_DIR} && ./scripts/auto_update.sh >> ${LOG_DIR}/cron.log 2>&1" >> /tmp/cron_tmp.txt
        echo "✅ 已配置自定义定时任务: ${CUSTOM_CRON}"
        ;;
    0)
        echo "✅ 已删除所有 ST Picker Android 定时任务"
        ;;
    *)
        echo "❌ 无效选项"
        rm -f /tmp/cron_tmp.txt
        exit 1
        ;;
esac

# 应用新的 crontab
crontab /tmp/cron_tmp.txt
rm -f /tmp/cron_tmp.txt

echo ""
echo "当前完整定时任务:"
crontab -l
echo ""

if [ "$CHOICE" != "0" ]; then
    echo "📋 手动测试命令:"
    echo "  cd ${PROJECT_DIR} && ./scripts/auto_update.sh"
    echo ""
    echo "📋 查看实时日志:"
    echo "  tail -f ${LOG_DIR}/cron.log"
    echo ""
    echo "⚠️  注意: macOS cron 需要给终端授「完整磁盘访问权限」"
    echo "   系统设置 → 隐私与安全性 → 完整磁盘访问权限 → 添加你的终端应用"
    echo ""
    echo "🔧 配置远程仓库 URL:"
    echo "   编辑 core/constants.py，设置 REMOTE_JSON_URL"
    echo "   示例: REMOTE_JSON_URL = 'https://gitee.com/用户名/仓库/raw/main/restructuring_watchlist.json'"
fi

echo ""
echo "========================================"
echo "  配置完成"
echo "========================================"
