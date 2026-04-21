#!/bin/bash
#
# ST Picker Android 版 - 数据自动更新脚本
# 功能：更新版本号 → 推送到远程仓库（GitHub/Gitee）
#
# 用法：
#   ./scripts/auto_update.sh              # 更新版本号 + 推送
#   ./scripts/auto_update.sh --sync       # 从鸿蒙版同步数据 + 更新版本号 + 推送
#   ./scripts/auto_update.sh --push-only  # 只推送当前 JSON（不更新版本号）
#

set -e

# 确保 cron 环境下能找到 python3
export PATH="/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
JSON_SOURCE="${PROJECT_DIR}/data/restructuring_watchlist.json"

# 鸿蒙版数据路径（用于同步）
HARMONY_JSON="/Volumes/Storage/st_picker_harmonyos/entry/src/main/resources/rawfile/restructuring_watchlist.json"

# 远程仓库配置（从 constants.py 中读取）
CONSTANTS_FILE="${PROJECT_DIR}/core/constants.py"
REMOTE_URL=$(grep "REMOTE_JSON_URL" "$CONSTANTS_FILE" | grep -oE '"https?://[^"]*"' | tr -d '"' || true)

# 从 URL 中提取仓库信息
# URL 格式: https://gitee.com/{user}/{repo}/raw/{branch}/restructuring_watchlist.json
#      或: https://raw.githubusercontent.com/{user}/{repo}/{branch}/restructuring_watchlist.json
REMOTE_TYPE=""
REMOTE_USER=""
REMOTE_REPO=""
REMOTE_BRANCH="main"

if [[ "$REMOTE_URL" =~ gitee\.com/([^/]+)/([^/]+)/raw/([^/]+)/ ]]; then
    REMOTE_TYPE="gitee"
    REMOTE_USER="${BASH_REMATCH[1]}"
    REMOTE_REPO="${BASH_REMATCH[2]}"
    REMOTE_BRANCH="${BASH_REMATCH[3]}"
elif [[ "$REMOTE_URL" =~ raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/ ]]; then
    REMOTE_TYPE="github"
    REMOTE_USER="${BASH_REMATCH[1]}"
    REMOTE_REPO="${BASH_REMATCH[2]}"
    REMOTE_BRANCH="${BASH_REMATCH[3]}"
fi

# 日志
LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/auto_update_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1" | tee -a "$LOG_FILE"
}

warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ $1" | tee -a "$LOG_FILE"
}

# ============================================================
# 参数解析
# ============================================================
UPDATE_VERSION=true
RUN_PUSH=true
SYNC_FROM_HARMONY=false

for arg in "$@"; do
    case "$arg" in
        --sync)
            SYNC_FROM_HARMONY=true
            UPDATE_VERSION=true
            RUN_PUSH=true
            ;;
        --push-only)
            UPDATE_VERSION=false
            RUN_PUSH=true
            SYNC_FROM_HARMONY=false
            ;;
        --version-only)
            UPDATE_VERSION=true
            RUN_PUSH=false
            SYNC_FROM_HARMONY=false
            ;;
        --help|-h)
            echo "用法: $0 [--sync | --push-only | --version-only]"
            echo "  --sync         从鸿蒙版同步数据 + 更新版本号 + 推送"
            echo "  --push-only    只推送当前 JSON（不更新版本号）"
            echo "  --version-only 只更新版本号（不推送）"
            echo "  默认           更新版本号 + 推送"
            exit 0
            ;;
    esac
done

log "========================================"
log "ST Picker Android 自动更新启动"
log "========================================"
log "模式: sync=${SYNC_FROM_HARMONY}, version=${UPDATE_VERSION}, push=${RUN_PUSH}"

# ============================================================
# 步骤 0: 从鸿蒙版同步数据（可选）
# ============================================================
if [ "$SYNC_FROM_HARMONY" = true ]; then
    log ""
    log "🔄 [0/3] 从鸿蒙版同步数据..."
    
    if [ ! -f "$HARMONY_JSON" ]; then
        error "找不到鸿蒙版数据文件: $HARMONY_JSON"
        error "请确认鸿蒙版项目路径正确"
        exit 1
    fi
    
    # 复制鸿蒙版数据
    cp "$HARMONY_JSON" "$JSON_SOURCE"
    log "✅ 已同步鸿蒙版数据"
    
    # 统计股票数量
    STOCK_COUNT=$(python3 -c "import json; d=json.load(open('$JSON_SOURCE')); print(len(d.get('restructuring_stocks',[])))" 2>/dev/null || echo "0")
    log "   股票数量: $STOCK_COUNT 只"
fi

# ============================================================
# 步骤 1: 更新版本号
# ============================================================
if [ "$UPDATE_VERSION" = true ]; then
    log ""
    log "🏷️  [1/3] 更新数据版本号..."
    
    if [ ! -f "$JSON_SOURCE" ]; then
        error "找不到源数据文件: $JSON_SOURCE"
        exit 1
    fi
    
    NEW_VERSION=$(date +"%Y-%m-%dT%H:%M:%S")
    CURRENT_VERSION=$(python3 -c "import json; d=json.load(open('$JSON_SOURCE')); print(d.get('data_version','未设置'))" 2>/dev/null || echo "未知")
    
    log "当前版本: $CURRENT_VERSION"
    log "新版本:   $NEW_VERSION"
    
    python3 << EOF >> "$LOG_FILE" 2>&1
import json
import sys

with open('$JSON_SOURCE', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['data_version'] = '$NEW_VERSION'
data['metadata'] = data.get('metadata', {})
data['metadata']['last_updated'] = '$NEW_VERSION'
data['metadata']['source'] = 'ST重整选股工具 - Android版'
data['stock_count'] = len(data.get('restructuring_stocks', []))

with open('$JSON_SOURCE', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 已更新 data_version: {data['data_version']}")
print(f"✅ 股票数量: {data['stock_count']}")
EOF
fi

# ============================================================
# 步骤 2: 数据质量校验
# ============================================================
log ""
log "🔍 [2/3] 数据质量校验..."

python3 << EOF >> "$LOG_FILE" 2>&1
import json
import sys

try:
    with open('$JSON_SOURCE', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stocks = data.get('restructuring_stocks', [])
    errors = []
    
    # 检查必要字段
    required_fields = ['stock_code', 'stock_name', 'current_stage']
    for i, stock in enumerate(stocks):
        for field in required_fields:
            if field not in stock:
                errors.append(f"股票[{i}] 缺少字段: {field}")
    
    # 检查是否有 data_version
    if 'data_version' not in data:
        errors.append("缺少 data_version 字段")
    
    # 检查股票数量
    if len(stocks) == 0:
        errors.append("股票列表为空")
    
    if errors:
        print("⚠️  质量校验发现警告:")
        for err in errors:
            print(f"   - {err}")
        sys.exit(0)  # 警告但不阻止
    else:
        print(f"✅ 质量校验通过 ({len(stocks)} 只股票)")
        
except Exception as e:
    print(f"❌ 质量校验失败: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    error "质量校验未通过"
    exit 1
fi

# ============================================================
# 步骤 3: 推送到远程仓库
# ============================================================
if [ "$RUN_PUSH" = true ]; then
    log ""
    log "🚀 [3/3] 推送到远程仓库..."
    
    if [ -z "$REMOTE_URL" ]; then
        error "REMOTE_JSON_URL 未配置"
        error "请在 core/constants.py 中设置远程仓库 URL"
        log ""
        log "配置示例:"
        log "  REMOTE_JSON_URL = 'https://gitee.com/用户名/仓库/raw/main/restructuring_watchlist.json'"
        log "  REMOTE_JSON_URL = 'https://raw.githubusercontent.com/用户名/仓库/main/restructuring_watchlist.json'"
        exit 1
    fi
    
    if [ -z "$REMOTE_TYPE" ] || [ -z "$REMOTE_USER" ] || [ -z "$REMOTE_REPO" ]; then
        error "无法从 REMOTE_JSON_URL 解析仓库信息"
        error "URL 格式应为:"
        error "  Gitee:  https://gitee.com/{user}/{repo}/raw/{branch}/file.json"
        error "  GitHub: https://raw.githubusercontent.com/{user}/{repo}/{branch}/file.json"
        exit 1
    fi
    
    log "远程仓库: $REMOTE_TYPE/$REMOTE_USER/$REMOTE_REPO ($REMOTE_BRANCH)"
    
    # 检查本地 Git 仓库
    GITEE_REPO_DIR="${PROJECT_DIR}/.remote-repo"
    
    if [ "$REMOTE_TYPE" = "gitee" ]; then
        REMOTE_GIT_URL="https://gitee.com/${REMOTE_USER}/${REMOTE_REPO}.git"
    else
        REMOTE_GIT_URL="https://github.com/${REMOTE_USER}/${REMOTE_REPO}.git"
    fi
    
    # 确保本地仓库存在
    if [ ! -d "${GITEE_REPO_DIR}/.git" ]; then
        log "克隆远程仓库到 ${GITEE_REPO_DIR}..."
        mkdir -p "$GITEE_REPO_DIR"
        git clone "$REMOTE_GIT_URL" "$GITEE_REPO_DIR" 2>&1 | tee -a "$LOG_FILE" || {
            error "克隆失败，请检查网络或仓库权限"
            exit 1
        }
        cd "$GITEE_REPO_DIR"
        git config user.email "auto@stpicker.local"
        git config user.name "ST Picker Auto"
    else
        cd "$GITEE_REPO_DIR"
        log "拉取最新代码..."
        git pull origin "$REMOTE_BRANCH" 2>&1 | tee -a "$LOG_FILE" || warn "git pull 失败，继续"
    fi
    
    # 复制更新后的 JSON
    cp "$JSON_SOURCE" "${GITEE_REPO_DIR}/restructuring_watchlist.json"
    
    # 检查是否有变更
    cd "$GITEE_REPO_DIR"
    if git diff --quiet -- restructuring_watchlist.json 2>/dev/null; then
        log "📄 JSON 文件无变化，跳过推送"
    else
        NEW_VERSION=$(date +"%Y-%m-%dT%H:%M:%S")
        git add restructuring_watchlist.json
        git commit -m "auto: update data ${NEW_VERSION}" 2>&1 | tee -a "$LOG_FILE"
        
        # 推送
        if git push origin "$REMOTE_BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ 推送成功: ${REMOTE_GIT_URL}"
            log ""
            log "📱 App 将在下次启动或点击更新按钮时自动拉取新数据"
        else
            error "推送失败，请检查网络或权限"
            error "如果使用 HTTPS，请确保已配置 credential helper 或 .netrc"
            exit 1
        fi
    fi
fi

log ""
log "========================================"
log "✅ 自动更新流程完成"
log "========================================"
log "日志文件: $LOG_FILE"
log ""

exit 0
