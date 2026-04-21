"""
ST选股工具 - 常量定义（添加类型注解）
集中管理所有阶段、颜色、主题等常量
"""

from typing import Dict, Tuple, List


# ─── 重整阶段定义 ──────────────────────────────────────────────

class Stage:
    """重整阶段枚举"""
    WATCHLIST: str = 'STAGE_0_WATCHLIST'
    APPLIED: str = 'STAGE_1_APPLIED'
    PRE_REORG: str = 'STAGE_2_PRE_REORG'
    RECRUITING: str = 'STAGE_3_RECRUITING'
    SELECTED: str = 'STAGE_4_SELECTED'
    AGREEMENT: str = 'STAGE_5_AGREEMENT'
    COURT_ACCEPT: str = 'STAGE_6_COURT_ACCEPT'
    PLAN_DISCLOSED: str = 'STAGE_7_PLAN_DISCLOSED'
    COURT_APPROVED: str = 'STAGE_8_COURT_APPROVED'
    EXECUTING: str = 'STAGE_9_EXECUTING'
    COMPLETED: str = 'STAGE_10_COMPLETED'


# 阶段中文名称映射
STAGE_NAMES: Dict[str, str] = {
    Stage.WATCHLIST: '观察名单',
    Stage.APPLIED: '被申请重整',
    Stage.PRE_REORG: '预重整受理',
    Stage.RECRUITING: '投资人招募',
    Stage.SELECTED: '投资人确定',
    Stage.AGREEMENT: '签订协议',
    Stage.COURT_ACCEPT: '法院受理',
    Stage.PLAN_DISCLOSED: '计划披露',
    Stage.COURT_APPROVED: '法院批准',
    Stage.EXECUTING: '执行中',
    Stage.COMPLETED: '重整完成',
}

# 阶段优先级（数字越小越优先 = 越佳介入时机）
STAGE_PRIORITY: Dict[str, int] = {
    Stage.RECRUITING: 1,
    Stage.SELECTED: 2,
    Stage.AGREEMENT: 3,
    Stage.COURT_ACCEPT: 4,
    Stage.PLAN_DISCLOSED: 5,
    Stage.COURT_APPROVED: 6,
    Stage.EXECUTING: 7,
    Stage.COMPLETED: 8,
    Stage.PRE_REORG: 9,
    Stage.APPLIED: 10,
    Stage.WATCHLIST: 11,
}

# 最佳介入阶段
BEST_ENTRY_STAGES: List[str] = [
    Stage.RECRUITING,
    Stage.SELECTED,
    Stage.AGREEMENT,
    Stage.COURT_ACCEPT,
]

# 投资建议映射
RECOMMENDATIONS: Dict[str, Tuple[str, str]] = {
    Stage.RECRUITING: ('🔥 最佳介入点', 'hot'),
    Stage.SELECTED: ('🔥 最佳介入点', 'hot'),
    Stage.AGREEMENT: ('📊 较好介入点', 'good'),
    Stage.COURT_ACCEPT: ('📊 较好介入点', 'good'),
    Stage.PLAN_DISCLOSED: ('✅ 确定性较高', 'safe'),
    Stage.COURT_APPROVED: ('✅ 确定性较高', 'safe'),
    Stage.EXECUTING: ('📈 执行中', 'info'),
    Stage.COMPLETED: ('📈 已完成', 'info'),
    Stage.APPLIED: ('⚠️ 早期阶段', 'warn'),
    Stage.PRE_REORG: ('⚠️ 早期阶段', 'warn'),
    Stage.WATCHLIST: ('👀 观察中', 'muted'),
}

# 风险等级映射
RISK_LEVELS: Dict[str, str] = {
    Stage.RECRUITING: '中高',
    Stage.SELECTED: '中高',
    Stage.AGREEMENT: '中',
    Stage.COURT_ACCEPT: '中',
    Stage.PLAN_DISCLOSED: '中低',
    Stage.COURT_APPROVED: '中低',
    Stage.EXECUTING: '低',
    Stage.COMPLETED: '低',
    Stage.APPLIED: '高',
    Stage.PRE_REORG: '中高',
    Stage.WATCHLIST: '极高',
}


# ─── 筛选选项 ──────────────────────────────────────────────────

# 阶段筛选下拉选项 -> 对应筛选值
FILTER_STAGE_OPTIONS: Dict[str, str] = {
    '全部': 'all',
    '最佳介入点': 'best',
    '投资人招募': Stage.RECRUITING,
    '投资人确定': Stage.SELECTED,
    '法院受理': Stage.COURT_ACCEPT,
    '计划披露': Stage.PLAN_DISCLOSED,
    '重整完成': Stage.COMPLETED,
}

# 排序选项
SORT_OPTIONS: Dict[str, str] = {
    '阶段优先': 'priority',
    '价格升序': 'price_asc',
    '价格降序': 'price_desc',
    '评分最高': 'score_desc',
}


# ─── 深色主题配色 ──────────────────────────────────────────────

class Theme:
    """深色主题配色 v2.0 - 现代化设计系统"""

    # 背景色 - 深邃蓝黑色调
    BG_PRIMARY: Tuple[float, float, float, float] = (0.051, 0.063, 0.082, 1)       # #0D1015
    BG_SECONDARY: Tuple[float, float, float, float] = (0.075, 0.090, 0.110, 1)     # #13171C
    BG_TERTIARY: Tuple[float, float, float, float] = (0.098, 0.114, 0.137, 1)      # #191D23
    BG_ELEVATED: Tuple[float, float, float, float] = (0.122, 0.141, 0.165, 1)      # #1F242A
    BG_CARD: Tuple[float, float, float, float] = (0.110, 0.129, 0.153, 0.95)       # 卡片背景

    # 文字色 - 精心调配的对比度
    TEXT_PRIMARY: Tuple[float, float, float, float] = (0.95, 0.96, 0.97, 1)        # #F2F5F8
    TEXT_SECONDARY: Tuple[float, float, float, float] = (0.70, 0.74, 0.78, 1)      # #B3BCC7
    TEXT_TERTIARY: Tuple[float, float, float, float] = (0.52, 0.56, 0.62, 1)       # #858F9E
    TEXT_MUTED: Tuple[float, float, float, float] = (0.38, 0.42, 0.48, 1)          # #616B7A
    TEXT_HINT: Tuple[float, float, float, float] = (0.28, 0.32, 0.38, 1)           # #485261

    # 强调色 - 活力蓝绿色系
    ACCENT_BLUE: Tuple[float, float, float, float] = (0.25, 0.65, 1.0, 1)          # #40A6FF
    ACCENT_RED: Tuple[float, float, float, float] = (1.0, 0.35, 0.35, 1)           # #FF5A5A
    ACCENT_GREEN: Tuple[float, float, float, float] = (0.25, 0.85, 0.50, 1)        # #40D980
    ACCENT_ORANGE: Tuple[float, float, float, float] = (1.0, 0.65, 0.20, 1)        # #FFA633
    ACCENT_PURPLE: Tuple[float, float, float, float] = (0.75, 0.45, 1.0, 1)        # #BF73FF
    ACCENT_YELLOW: Tuple[float, float, float, float] = (1.0, 0.85, 0.25, 1)        # #FFD940

    # 阶段颜色
    STAGE_HOT: Tuple[float, float, float, float] = (1.0, 0.35, 0.35, 1)            # 最佳介入 - 红色
    STAGE_GOOD: Tuple[float, float, float, float] = (1.0, 0.65, 0.20, 1)           # 较好 - 橙色
    STAGE_SAFE: Tuple[float, float, float, float] = (0.25, 0.85, 0.50, 1)          # 确定性高 - 绿色
    STAGE_INFO: Tuple[float, float, float, float] = (0.25, 0.65, 1.0, 1)           # 执行/完成 - 蓝色
    STAGE_WARN: Tuple[float, float, float, float] = (1.0, 0.85, 0.25, 1)           # 早期 - 黄色
    STAGE_MUTED: Tuple[float, float, float, float] = (0.52, 0.56, 0.62, 1)         # 观察 - 灰色

    # 阶段左侧竖条颜色映射
    STAGE_COLORS: Dict[str, Tuple[float, float, float, float]] = {
        'hot': STAGE_HOT,
        'good': STAGE_GOOD,
        'safe': STAGE_SAFE,
        'info': STAGE_INFO,
        'warn': STAGE_WARN,
        'muted': STAGE_MUTED,
    }

    # 按钮色
    BTN_PRIMARY: Tuple[float, float, float, float] = (0.20, 0.55, 0.95, 1)         # #2D8CF0
    BTN_PRIMARY_HOVER: Tuple[float, float, float, float] = (0.25, 0.60, 1.0, 1)    # 主按钮悬停
    BTN_SECONDARY: Tuple[float, float, float, float] = (0.15, 0.18, 0.22, 1)       # 次按钮
    BTN_SUCCESS: Tuple[float, float, float, float] = (0.20, 0.70, 0.45, 1)         # 成功按钮
    BTN_DANGER: Tuple[float, float, float, float] = (0.85, 0.30, 0.30, 1)          # 危险按钮

    # 分隔线
    DIVIDER: Tuple[float, float, float, float] = (0.18, 0.22, 0.28, 1)             # #2E3847
    DIVIDER_LIGHT: Tuple[float, float, float, float] = (1, 1, 1, 0.05)             # 亮色分隔线

    # 玻璃拟态效果
    GLASS_BG: Tuple[float, float, float, float] = (0.15, 0.18, 0.22, 0.7)          # 玻璃背景
    GLASS_BORDER: Tuple[float, float, float, float] = (1, 1, 1, 0.1)               # 玻璃边框
    GLASS_HIGHLIGHT: Tuple[float, float, float, float] = (1, 1, 1, 0.05)           # 玻璃高光

    # 阴影颜色
    SHADOW_LIGHT: Tuple[float, float, float, float] = (0, 0, 0, 0.15)
    SHADOW_MEDIUM: Tuple[float, float, float, float] = (0, 0, 0, 0.25)
    SHADOW_HEAVY: Tuple[float, float, float, float] = (0, 0, 0, 0.40)

    # 圆角半径
    CARD_RADIUS: int = 12
    BADGE_RADIUS: int = 6
    BUTTON_RADIUS: int = 8
    RADIUS_SMALL: int = 6
    RADIUS_MEDIUM: int = 10
    RADIUS_LARGE: int = 16


# ─── 资产注入预期 ──────────────────────────────────────────────

ASSET_INJECTION: Dict[str, str] = {
    'confirmed_plan': '✅ 已确认注入计划',
    'strong_expectation': '🔶 有较强注入预期',
    'possible': '🔸 可能注入',
    'none': '❌ 无注入预期',
}


# ─── 远程 JSON 热更新配置 ──────────────────────────────────────

# 远程 JSON URL（支持 GitHub Raw / Gitee Raw / CDN）
# 示例:
#   GitHub: 'https://raw.githubusercontent.com/用户名/仓库/main/restructuring_watchlist.json'
#   Gitee:  'https://gitee.com/用户名/仓库/raw/main/restructuring_watchlist.json'
REMOTE_JSON_URL: str = 'https://raw.githubusercontent.com/Diwild/st-picker-android/main/data/restructuring_watchlist.json'
