# ST选股工具 - Android APK版本 v3.0

## 📱 应用简介

ST选股工具Android版是一个基于Kivy框架开发的移动应用，用于查看和分析A股ST重整股票。

### 主要功能

- 📊 查看ST重整股票列表（8只内置数据）
- 🔍 多维度筛选：阶段、价格区间、产业投资人、关键字搜索
- 📈 投资人质量评分分析（0-100分）
- 🔥 最佳介入时机推荐
- 📋 股票详情页：重整时间线、投资人详情、方案信息
- 🎨 深色主题 + 现代卡片 UI
- 📱 纯离线运行，无需网络

## 📁 项目结构

```
st_picker_android/
├── main.py                     # 入口文件（精简）
├── buildozer.spec              # Android 构建配置
├── build_apk.py                # APK 构建脚本
│
├── core/                       # 核心业务逻辑层
│   ├── __init__.py
│   ├── constants.py            # 阶段、主题、颜色等常量
│   ├── models.py               # 数据模型（Stock, Investor, Scheme）
│   ├── analyzer.py             # 股票分析器（评分、筛选、排序）
│   └── data_manager.py         # 数据加载/导入管理
│
├── ui/                         # UI 层
│   ├── __init__.py
│   ├── app.py                  # Kivy App 主类 + 页面管理
│   ├── screens/
│   │   ├── main_screen.py      # 主屏幕（列表+筛选）
│   │   └── detail_screen.py    # 股票详情页
│   └── widgets/
│       ├── stock_card.py       # 股票卡片组件
│       ├── filter_panel.py     # 可折叠筛选面板
│       ├── stage_badge.py      # 阶段标签组件
│       └── score_bar.py        # 评分进度条
│
├── data/
│   └── restructuring_watchlist.json  # 股票数据
│
├── assets/
│   └── fonts/                  # 中文字体（可选）
│
└── README_ANDROID.md
```

## 🏛 架构设计

采用分层架构，核心层与 UI 层完全分离：

```
┌─────────────────────────────┐
│         UI Layer            │
│   app.py / screens / widgets│
├─────────────────────────────┤
│        Core Layer           │
│  analyzer / models / data   │
├─────────────────────────────┤
│        Data Layer           │
│     JSON / sample data      │
└─────────────────────────────┘
```

## 🚀 本地运行

### 环境准备

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install kivy pillow
```

### 运行应用

```bash
source .venv/bin/activate
python main.py
```

## 📦 构建 Android APK

### 方式1: GitHub Actions（推荐）

1. 推送到 GitHub 仓库
2. Actions 自动构建 APK
3. 在 Actions 页面下载

### 方式2: Docker 构建

```bash
docker pull kivy/buildozer
docker run --rm -v $(pwd):/home/user/app kivy/buildozer android debug
```

### 方式3: 本地构建（仅 Linux）

```bash
pip install buildozer cython
buildozer android debug
```

## 🔧 自定义数据

编辑 `data/restructuring_watchlist.json`，格式参考现有数据。

## 📱 系统要求

- **Android**: 5.0+ (API 21)
- **存储**: 约 20MB
- **网络**: 不需要（离线应用）

## ⚠️ 重要声明

1. ST/*ST股票投资具有极高风险
2. 本工具仅供学习研究使用，不构成投资建议
3. 数据仅供参考，投资前请自行核实

## 📄 开源协议

MIT License

---

**版本**: 3.0.0 | **更新**: 2026-04-03
