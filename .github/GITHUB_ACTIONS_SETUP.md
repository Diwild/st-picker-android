# GitHub Actions 自动更新配置指南

## 概述

使用 GitHub Actions 实现每天自动更新远程 JSON 数据，无需本地 Mac 24 小时开机。

## 文件说明

```
.github/
├── workflows/
│   └── auto-update.yml       # GitHub Actions 工作流（定时触发）
├── scripts/
│   └── update_data.py        # 数据更新脚本
└── GITHUB_ACTIONS_SETUP.md   # 本文件
```

## 配置步骤

### 第一步：将代码推送到 GitHub

```bash
cd /Users/mlfe/st_picker_build

# 初始化 Git 仓库（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 推送到 GitHub（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

### 第二步：配置远程 JSON URL

编辑 `core/constants.py`，设置 GitHub Raw URL：

```python
# GitHub Raw URL 格式：
# https://raw.githubusercontent.com/用户名/仓库名/分支名/文件路径
REMOTE_JSON_URL: str = 'https://raw.githubusercontent.com/你的用户名/st-picker-data/main/data/restructuring_watchlist.json'
```

### 第三步：测试工作流

进入 GitHub 仓库页面 → Actions → Auto Update Data → Run workflow → Run workflow

手动触发一次，确认流程正常。

### 第四步：观察定时执行

工作流会在以下时间自动执行：

| 时间 | 说明 |
|------|------|
| 每天 15:30 (UTC+8) | 仅工作日（周一到周五） |
| 手动触发 | 随时通过 GitHub 页面触发 |

## 高级配置

### 从鸿蒙版同步数据

如果你希望 GitHub Actions 先从鸿蒙版拉取最新数据，再更新版本号：

1. 在 GitHub 仓库 Settings → Secrets and variables → Variables 中添加：
   - 变量名：`HARMONY_JSON_URL`
   - 值：`https://gitee.com/你的用户名/你的仓库/raw/main/restructuring_watchlist.json`

2. 手动触发时选择 "sync_from_harmony = true"

### 修改定时时间

编辑 `.github/workflows/auto-update.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '30 7 * * 1-5'   # 15:30 北京时间，工作日
  - cron: '0 1 * * *'      # 09:00 北京时间，每天
```

> 注意：GitHub Actions 使用 UTC 时间，北京时间 = UTC + 8 小时

## 常见问题

**Q: GitHub Actions 免费额度够用吗？**
A: 公共仓库无限制。私有仓库每月 2000 分钟（本工作流每次约 30 秒，足够用）。

**Q: 数据没变会重复提交吗？**
A: 不会。脚本会检查是否有变更，无变更则跳过提交。

**Q: 推送失败怎么办？**
A: 检查 GitHub Token 权限。工作流已配置 `permissions: contents: write`，一般无需额外设置。

**Q: 如何查看执行日志？**
A: GitHub 仓库 → Actions → 点击具体运行记录 → 查看每个步骤的日志输出。
