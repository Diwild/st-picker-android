#!/usr/bin/env python3
"""
ST Picker 数据更新脚本 - GitHub Actions 版本
功能：
  - 更新 data_version 时间戳
  - 可选从鸿蒙版同步数据
  - 数据质量校验
  - 保存更新后的 JSON

用法：
  python update_data.py                    # 仅更新版本号
  python update_data.py --sync-from-harmony # 从鸿蒙版同步 + 更新版本号
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List
import argparse
import requests

# 配置
JSON_PATH = "data/restructuring_watchlist.json"
HARMONY_JSON_URL = os.environ.get("HARMONY_JSON_URL", "")


def log(message: str) -> None:
    """输出日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def load_json(path: str) -> Dict[str, Any]:
    """加载 JSON 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    """保存 JSON 文件（原子写入）"""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def sync_from_harmony() -> bool:
    """从鸿蒙版同步数据"""
    if not HARMONY_JSON_URL:
        log("⚠️  HARMONY_JSON_URL 未配置，跳过同步")
        log("   如需同步，请在 GitHub 仓库 Settings > Secrets and variables > Variables 中设置")
        return False
    
    log(f"🔄 从鸿蒙版同步数据...")
    log(f"   URL: {HARMONY_JSON_URL[:60]}...")
    
    try:
        response = requests.get(HARMONY_JSON_URL, timeout=30)
        response.raise_for_status()
        
        harmony_data = response.json()
        
        # 验证数据格式
        if "restructuring_stocks" not in harmony_data:
            log("❌ 鸿蒙版数据格式错误：缺少 restructuring_stocks 字段")
            return False
        
        # 保存同步的数据
        save_json(JSON_PATH, harmony_data)
        
        stock_count = len(harmony_data.get("restructuring_stocks", []))
        log(f"✅ 已同步鸿蒙版数据，股票数量: {stock_count}")
        return True
        
    except requests.exceptions.RequestException as e:
        log(f"❌ 同步失败（网络错误）: {e}")
        return False
    except json.JSONDecodeError as e:
        log(f"❌ 同步失败（JSON 解析错误）: {e}")
        return False
    except Exception as e:
        log(f"❌ 同步失败: {e}")
        return False


def validate_data(data: Dict[str, Any]) -> List[str]:
    """数据质量校验，返回错误列表"""
    errors = []
    
    stocks = data.get("restructuring_stocks", [])
    
    # 检查必要字段
    required_fields = ["stock_code", "stock_name", "current_stage"]
    for i, stock in enumerate(stocks):
        for field in required_fields:
            if field not in stock:
                errors.append(f"股票[{i}] 缺少字段: {field}")
    
    # 检查是否有 data_version
    if "data_version" not in data:
        errors.append("缺少 data_version 字段")
    
    # 检查股票数量
    if len(stocks) == 0:
        errors.append("股票列表为空")
    
    return errors


def update_version(data: Dict[str, Any]) -> str:
    """更新版本号，返回新版本"""
    new_version = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    data["data_version"] = new_version
    data["metadata"] = data.get("metadata", {})
    data["metadata"]["last_updated"] = new_version
    data["metadata"]["source"] = "ST重整选股工具 - GitHub Actions 自动更新"
    data["stock_count"] = len(data.get("restructuring_stocks", []))
    
    return new_version


def main():
    parser = argparse.ArgumentParser(description="ST Picker 数据更新脚本")
    parser.add_argument(
        "--sync-from-harmony",
        action="store_true",
        help="从鸿蒙版同步数据后再更新版本号"
    )
    args = parser.parse_args()
    
    log("=" * 50)
    log("ST Picker 数据更新启动")
    log("=" * 50)
    
    # 步骤 1: 同步数据（可选）
    if args.sync_from_harmony:
        if not sync_from_harmony():
            log("⚠️  同步失败，将使用本地现有数据")
    
    # 步骤 2: 加载数据
    log("")
    log(f"📂 加载数据: {JSON_PATH}")
    
    if not os.path.exists(JSON_PATH):
        log(f"❌ 数据文件不存在: {JSON_PATH}")
        sys.exit(1)
    
    try:
        data = load_json(JSON_PATH)
    except Exception as e:
        log(f"❌ 加载数据失败: {e}")
        sys.exit(1)
    
    old_version = data.get("data_version", "未设置")
    stock_count = len(data.get("restructuring_stocks", []))
    log(f"   当前版本: {old_version}")
    log(f"   股票数量: {stock_count}")
    
    # 步骤 3: 更新版本号
    log("")
    log("🏷️  更新版本号...")
    new_version = update_version(data)
    log(f"   新版本: {new_version}")
    
    # 步骤 4: 质量校验
    log("")
    log("🔍 数据质量校验...")
    errors = validate_data(data)
    
    if errors:
        log(f"⚠️  发现 {len(errors)} 个问题:")
        for err in errors:
            log(f"   - {err}")
        # 警告但不阻止
    else:
        log(f"✅ 校验通过 ({stock_count} 只股票)")
    
    # 步骤 5: 保存数据
    log("")
    log(f"💾 保存数据...")
    try:
        save_json(JSON_PATH, data)
        log(f"✅ 已保存: {JSON_PATH}")
    except Exception as e:
        log(f"❌ 保存失败: {e}")
        sys.exit(1)
    
    log("")
    log("=" * 50)
    log("✅ 数据更新完成")
    log("=" * 50)
    log(f"版本: {old_version} → {new_version}")
    log(f"股票: {stock_count} 只")
    
    # 输出到 GitHub Actions
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"new_version={new_version}\n")
            f.write(f"stock_count={stock_count}\n")


if __name__ == "__main__":
    main()
