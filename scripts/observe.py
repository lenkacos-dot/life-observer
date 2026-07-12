#!/usr/bin/env python3
"""
人生观察员 — 记录模块
========================
记录你的情绪、消费、关系、习惯、想法等日常观察。
纯 stdlib，零依赖，跨平台。

用法:
  python3 observe.py 记录 "今天加班到很晚，觉得特别焦虑" --category emotion --intensity 7
  python3 observe.py 记录 "买了一杯奶茶" --category spend --intensity 3 --tags 奶茶,消费
  python3 observe.py 记录 "和女朋友吵架了" --category relationship --intensity 8
  python3 observe.py 列表 [--category emotion] [--days 7]
  python3 observe.py 统计 [--days 30]
  python3 observe.py 删除 <id>
"""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# ── 路径 ──────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DATA_FILE = os.path.join(DATA_DIR, "observations.json")

# ── 类别定义 ──────────────────────────────────────────────────────
CATEGORIES = {
    "emotion":      "情绪 / 心情",
    "spend":        "消费 / 支出",
    "relationship": "关系 / 人际",
    "habit":        "习惯 / 行为",
    "thought":      "想法 / 思考",
    "health":       "健康 / 身体",
    "other":        "其他",
}

CATEGORY_ICONS = {
    "emotion":      "😊",
    "spend":        "💰",
    "relationship": "🤝",
    "habit":        "🔄",
    "thought":      "💡",
    "health":       "🏥",
    "other":        "📌",
}

# ── 数据层 ────────────────────────────────────────────────────────

def _ensure_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"observations": []}, f, ensure_ascii=False, indent=2)


def _load():
    _ensure_data()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    _ensure_data()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_observation(content, category="other", intensity=5, tags=None):
    """添加一条观察记录"""
    data = _load()
    record = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now().isoformat(),
        "category": category if category in CATEGORIES else "other",
        "content": content.strip(),
        "intensity": max(1, min(10, intensity)),
        "tags": tags or [],
    }
    data["observations"].append(record)
    _save(data)
    return record


def list_observations(category=None, days=None, limit=50):
    """列出观察记录，可选过滤"""
    data = _load()
    obs = data["observations"]

    # 时间过滤
    if days is not None:
        cutoff = datetime.now() - timedelta(days=days)
        obs = [o for o in obs if datetime.fromisoformat(o["timestamp"]) >= cutoff]

    # 类别过滤
    if category:
        obs = [o for o in obs if o["category"] == category]

    # 按时间倒序
    obs.sort(key=lambda o: o["timestamp"], reverse=True)
    return obs[:limit]


def stats(days=30):
    """统计指定天数的观察数据"""
    cutoff = datetime.now() - timedelta(days=days)
    data = _load()
    obs = [o for o in data["observations"]
           if datetime.fromisoformat(o["timestamp"]) >= cutoff]

    # 总览
    total = len(obs)
    if total == 0:
        return {"total": 0, "days": days, "categories": {}, "top_tags": [], "avg_intensity": 0}

    # 按类别统计
    cat_counts = Counter(o["category"] for o in obs)
    cat_intensities = defaultdict(list)
    for o in obs:
        cat_intensities[o["category"]].append(o["intensity"])

    categories = {}
    for cat in CATEGORIES:
        if cat in cat_counts:
            intensities = cat_intensities[cat]
            categories[cat] = {
                "count": cat_counts[cat],
                "avg_intensity": round(sum(intensities) / len(intensities), 1),
                "icon": CATEGORY_ICONS.get(cat, "📌"),
                "label": CATEGORIES[cat],
            }

    # 标签统计
    all_tags = [t for o in obs for t in o.get("tags", [])]
    top_tags = Counter(all_tags).most_common(10)

    # 平均强度
    avg_intensity = round(sum(o["intensity"] for o in obs) / total, 1)

    # 每日记录数（检测行为模式）
    daily_counts = Counter(
        datetime.fromisoformat(o["timestamp"]).strftime("%Y-%m-%d")
        for o in obs
    )

    return {
        "total": total,
        "days": days,
        "categories": categories,
        "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
        "avg_intensity": avg_intensity,
        # 哪天记录最多
        "most_recorded_day": max(daily_counts, key=daily_counts.get) if daily_counts else None,
        "most_recorded_day_count": max(daily_counts.values()) if daily_counts else 0,
        # 连续记录天数
        "active_days": len(daily_counts),
    }


def delete_observation(obs_id):
    """删除一条记录"""
    data = _load()
    before = len(data["observations"])
    data["observations"] = [o for o in data["observations"] if o["id"] != obs_id]
    if len(data["observations"]) == before:
        return False
    _save(data)
    return True


# ── CLI ───────────────────────────────────────────────────────────

def print_record(record):
    """打印一条记录"""
    icon = CATEGORY_ICONS.get(record["category"], "📌")
    ts = datetime.fromisoformat(record["timestamp"]).strftime("%m-%d %H:%M")
    tag_str = f"  #{' #'.join(record.get('tags', []))}" if record.get("tags") else ""
    bar = "█" * record["intensity"] + "░" * (10 - record["intensity"])
    print(f"  [{record['id']}] {icon} {ts} 强度 {bar} ({record['intensity']}/10)")
    print(f"         {CATEGORIES.get(record['category'], '其他')}: {record['content']}{tag_str}")
    print()


def cmd_add(args):
    """记录一条观察"""
    if not args:
        print("❌ 用法: observe.py 记录 \"内容\" [--category emotion] [--intensity 5] [--tags a,b,c]")
        sys.exit(1)

    content = args[0]
    category = "other"
    intensity = 5
    tags = []

    # 解析可选参数
    i = 1
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--intensity" and i + 1 < len(args):
            intensity = int(args[i + 1])
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags = [t.strip() for t in args[i + 1].split(",") if t.strip()]
            i += 2
        else:
            i += 1

    record = add_observation(content, category, intensity, tags)
    icon = CATEGORY_ICONS.get(record["category"], "📌")
    print(f"✅ 已记录 {icon} [{record['id']}]")
    print_record(record)


def cmd_list(args):
    """列出观察记录"""
    category = None
    days = None
    limit = 50

    i = 0
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    obs = list_observations(category, days, limit)
    if not obs:
        print("📭 暂无记录")
        return

    # 显示标题
    filters = []
    if category:
        filters.append(f"类别={category}")
    if days:
        filters.append(f"最近{days}天")
    title = f"📋 观察记录 {'(' + ', '.join(filters) + ')' if filters else ''}"
    print(title)
    print("─" * 60)

    for record in obs:
        print_record(record)

    print(f"共 {len(obs)} 条记录")


def cmd_stats(args):
    """统计报告"""
    days = 30
    if args and args[0].isdigit():
        days = int(args[0])

    s = stats(days)
    print(f"\n📊 人生观察统计 — 最近 {days} 天")
    print("═" * 50)

    if s["total"] == 0:
        print("📭 暂无数据，开始记录吧！")
        print("   python3 observe.py 记录 \"今天心情怎么样？\" --category emotion")
        return

    print(f"  📝 总记录数:     {s['total']}")
    print(f"  📅 有记录天数:   {s['active_days']}/{s['days']}")
    print(f"  📈 日均记录:     {s['total'] / s['days']:.1f} 条")
    print(f"  🎯 平均强度:     {s['avg_intensity']}/10")
    print()

    print(f"  📂 类别分布:")
    for cat, info in sorted(s["categories"].items(),
                            key=lambda x: x[1]["count"], reverse=True):
        bar_len = int(info["count"] / s["total"] * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        pct = info["count"] / s["total"] * 100
        print(f"    {info['icon']} {info['label']:8s} {bar} {info['count']:3d}条 ({pct:4.1f}%) 均强度{info['avg_intensity']}/10")

    if s["top_tags"]:
        print()
        print(f"  🏷️  高频标签:")
        for t in s["top_tags"][:5]:
            print(f"    #{t['tag']:12s} 出现 {t['count']} 次")

    print()


def cmd_delete(args):
    """删除一条记录"""
    if not args:
        print("❌ 用法: observe.py 删除 <id>")
        sys.exit(1)

    obs_id = args[0]
    if delete_observation(obs_id):
        print(f"✅ 已删除记录 [{obs_id}]")
    else:
        print(f"❌ 未找到记录 [{obs_id}]")


def cmd_categories(args):
    """列出所有类别"""
    print("📂 可用类别:")
    for key, label in CATEGORIES.items():
        icon = CATEGORY_ICONS.get(key, "📌")
        print(f"  {icon} {key:15s} → {label}")


def main():
    if len(sys.argv) < 2:
        print("人生观察员 — 记录模块")
        print()
        print("用法:")
        print("  observe.py 记录 <内容> [--category <类别>] [--intensity <1-10>] [--tags <tag1,tag2>]")
        print("  observe.py 列表 [--category <类别>] [--days <天数>] [--limit <数量>]")
        print("  observe.py 统计 [<天数>]")
        print("  observe.py 删除 <id>")
        print("  observe.py 类别")
        print()
        print("类别: emotion, spend, relationship, habit, thought, health, other")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "记录": cmd_add,
        "列表": cmd_list,
        "统计": cmd_stats,
        "删除": cmd_delete,
        "类别": cmd_categories,
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"❌ 未知命令: {cmd}")
        print("可用命令: 记录, 列表, 统计, 删除, 类别")
        sys.exit(1)


if __name__ == "__main__":
    main()