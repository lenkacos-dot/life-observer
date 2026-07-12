#!/usr/bin/env python3
"""
人生观察员 — 报告模块
========================
30 天后输出深度洞察报告。
它会告诉你：
- 你以为你在焦虑工作，实际上你 80% 的负面情绪来自……
- 你的消费模式透露了什么
- 你的人际关系变化趋势
- 你不想面对的那些真相

纯 stdlib，零依赖，跨平台。

用法:
  python3 report.py 30          # 30天洞察报告
  python3 report.py 7           # 7天周报
  python3 report.py 趋势        # 趋势分析
  python3 report.py 洞察        # 核心洞察摘要
"""

import json
import os
import sys
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# ── 路径 ──────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(SKILL_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "observations.json")

CATEGORIES = {
    "emotion":      ("情绪", "😊"),
    "spend":        ("消费", "💰"),
    "relationship": ("关系", "🤝"),
    "habit":        ("习惯", "🔄"),
    "thought":      ("想法", "💡"),
    "health":       ("健康", "🏥"),
    "other":        ("其他", "📌"),
}

# ── 情绪关键词映射（用于推测真实情绪来源）───────────────────────
EMOTION_KEYWORDS = {
    "工作":   ["加班", "工作", "项目", "老板", "同事", "KPI", "绩效", "deadline", "任务",
               "汇报", "会议", "业绩", "客户", "甲方", "乙方", "职场", "上班", "辞职"],
    "关系":   ["对象", "女朋友", "男朋友", "老婆", "老公", "家人", "父母", "朋友",
               "吵架", "冷战", "分手", "约会", "孤独", "社交", "被忽视"],
    "金钱":   ["钱", "收入", "工资", "存款", "房贷", "车贷", "账单", "信用卡",
               "借钱", "投资", "理财", "亏损", "消费降级"],
    "健康":   ["失眠", "头痛", "累", "疲惫", "生病", "身体", "体检", "焦虑",
               "压力", "抑郁", "emo", "难过", "烦躁"],
    "自我":   ["迷茫", "方向", "意义", "成长", "学习", "进步", "拖延", "懒",
               "内耗", "自我怀疑", "不自信", "瓶颈"],
}

# 正向情绪词
POSITIVE_WORDS = ["开心", "高兴", "快乐", "幸福", "满足", "感动", "感恩", "期待",
                  "兴奋", "放松", "平静", "舒服", "释然", "成就感", "进步", "突破"]

NEGATIVE_WORDS = ["焦虑", "烦躁", "难过", "生气", "愤怒", "失望", "沮丧", "累",
                  "疲惫", "压力", "emo", "抑郁", "痛苦", "崩溃", "厌倦", "无聊",
                  "孤独", "委屈", "不安", "害怕", "担心", "愧疚", "后悔", "伤心"]


# ── 数据加载 ──────────────────────────────────────────────────────

def load_observations(days=30):
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    cutoff = datetime.now() - timedelta(days=days)
    obs = []
    for o in data.get("observations", []):
        ts = datetime.fromisoformat(o["timestamp"])
        if ts >= cutoff:
            obs.append(o)
    obs.sort(key=lambda o: o["timestamp"])
    return obs


# ── 分析引擎 ──────────────────────────────────────────────────────

def analyze_emotions(obs):
    """情绪分析：正负比例、情绪来源推断"""
    emotion_obs = [o for o in obs if o["category"] == "emotion"]
    if not emotion_obs:
        return None

    # 正负判定
    positive = 0
    negative = 0
    neutral = 0
    for o in emotion_obs:
        text = o["content"]
        pos_count = sum(1 for w in POSITIVE_WORDS if w in text)
        neg_count = sum(1 for w in NEGATIVE_WORDS if w in text)
        if pos_count > neg_count:
            positive += 1
        elif neg_count > pos_count:
            negative += 1
        else:
            neutral += 1

    total_emo = len(emotion_obs)
    pos_pct = round(positive / total_emo * 100, 1) if total_emo else 0
    neg_pct = round(negative / total_emo * 100, 1) if total_emo else 0

    # 情绪强度趋势（是否在加重）
    intensities = [o["intensity"] for o in emotion_obs]
    if len(intensities) >= 4:
        half = len(intensities) // 2
        first_half = sum(intensities[:half]) / half
        second_half = sum(intensities[half:]) / (len(intensities) - half)
        trend = "上升" if second_half > first_half + 0.5 else (
            "下降" if second_half < first_half - 0.5 else "平稳"
        )
    else:
        trend = "数据不足"

    # 情绪来源推断（负面情绪的主要关联领域）
    negative_obs = [o for o in emotion_obs
                    if any(w in o["content"] for w in NEGATIVE_WORDS)]
    source_scores = defaultdict(float)
    for o in negative_obs:
        text = o["content"]
        for source, keywords in EMOTION_KEYWORDS.items():
            score = sum(1 for k in keywords if k in text)
            if score > 0:
                source_scores[source] += score * (o["intensity"] / 5.0)

    total_score = sum(source_scores.values())
    if total_score > 0:
        sources = sorted(
            source_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        source_pcts = [(s, round(c / total_score * 100, 1)) for s, c in sources]
    else:
        source_pcts = []

    # 高频情绪标签
    all_tags = [t for o in emotion_obs for t in o.get("tags", [])]
    top_tags = Counter(all_tags).most_common(5)

    return {
        "total": total_emo,
        "positive": positive,
        "positive_pct": pos_pct,
        "negative": negative,
        "negative_pct": neg_pct,
        "neutral": neutral,
        "avg_intensity": round(sum(intensities) / len(intensities), 1) if intensities else 0,
        "trend": trend,
        "source_scores": source_pcts,
        "top_tags": top_tags,
    }


def analyze_spending(obs):
    """消费分析"""
    spend_obs = [o for o in obs if o["category"] == "spend"]
    if not spend_obs:
        return None

    total = len(spend_obs)
    intensities = [o["intensity"] for o in spend_obs]
    avg_intensity = round(sum(intensities) / total, 1) if total else 0

    # 消费标签
    all_tags = [t for o in spend_obs for t in o.get("tags", [])]
    top_tags = Counter(all_tags).most_common(5)

    # 冲动消费比例（intensity高的视为冲动）
    impulsive = sum(1 for o in spend_obs if o["intensity"] >= 7)
    impulsive_pct = round(impulsive / total * 100, 1) if total else 0

    return {
        "total": total,
        "avg_intensity": avg_intensity,
        "impulsive": impulsive,
        "impulsive_pct": impulsive_pct,
        "top_tags": top_tags,
    }


def analyze_relationships(obs):
    """关系分析"""
    rel_obs = [o for o in obs if o["category"] == "relationship"]
    if not rel_obs:
        return None

    total = len(rel_obs)
    # 负面关系事件
    negative = sum(1 for o in rel_obs
                   if any(w in o["content"] for w in NEGATIVE_WORDS))
    positive = sum(1 for o in rel_obs
                   if any(w in o["content"] for w in POSITIVE_WORDS))
    negative_pct = round(negative / total * 100, 1) if total else 0
    positive_pct = round(positive / total * 100, 1) if total else 0

    # 关系关键词
    all_tags = [t for o in rel_obs for t in o.get("tags", [])]
    top_tags = Counter(all_tags).most_common(5)

    return {
        "total": total,
        "negative": negative,
        "negative_pct": negative_pct,
        "positive": positive,
        "positive_pct": positive_pct,
        "top_tags": top_tags,
    }


def analyze_correlations(obs):
    """相关性分析：情绪 ↔ 消费 / 关系 / 健康 之间的关联"""
    from collections import defaultdict

    def date_key(o):
        return datetime.fromisoformat(o["timestamp"]).strftime("%Y-%m-%d")

    daily = defaultdict(list)
    for o in obs:
        daily[date_key(o)].append(o)

    correlations = []
    days = sorted(daily.keys())

    # 检查：情绪差的日子是否消费更多
    bad_emotion_days = set()
    spend_days = set()
    for d in days:
        day_obs = daily[d]
        for o in day_obs:
            if o["category"] == "emotion" and o["intensity"] >= 6:
                if any(w in o["content"] for w in NEGATIVE_WORDS):
                    bad_emotion_days.add(d)
            if o["category"] == "spend":
                spend_days.add(d)

    if bad_emotion_days and spend_days:
        overlap = bad_emotion_days & spend_days
        if overlap:
            overlap_pct = round(len(overlap) / len(bad_emotion_days) * 100, 1)
            correlations.append(
                f"负面情绪天中有 {len(overlap)} 天同时有消费记录（{overlap_pct}%）"
            )
            # 检查是否冲动消费
            impulsive_on_bad = 0
            for d in overlap:
                for o in daily[d]:
                    if o["category"] == "spend" and o["intensity"] >= 7:
                        impulsive_on_bad += 1
            if impulsive_on_bad:
                correlations.append(
                    f"负面情绪天发生了 {impulsive_on_bad} 次冲动消费"
                )

    # 情绪与健康
    health_emotion_overlap = 0
    health_days = set()
    for d in days:
        for o in daily[d]:
            if o["category"] == "health":
                health_days.add(d)
    if bad_emotion_days and health_days:
        overlap = bad_emotion_days & health_days
        if overlap:
            health_emotion_overlap = len(overlap)
            correlations.append(
                f"负面情绪与健康问题在同一天出现 {health_emotion_overlap} 次"
            )

    # 关系与情绪
    rel_days = set()
    for d in days:
        for o in daily[d]:
            if o["category"] == "relationship":
                rel_days.add(d)
    if bad_emotion_days and rel_days:
        overlap = bad_emotion_days & rel_days
        if overlap:
            correlations.append(
                f"关系事件与负面情绪在同一天出现 {len(overlap)} 次"
            )

    return correlations


def generate_insight(obs, emo_analysis, spend_analysis, rel_analysis, correlations):
    """生成核心洞察：那个「你以为……实际上……」的结论"""
    insights = []

    if not emo_analysis or emo_analysis["total"] < 3:
        insights.append("📭 数据量不足，无法生成深度洞察。继续记录，30天后见分晓。")
        return insights

    # ── 核心洞察：负面情绪来源 ──
    if emo_analysis["source_scores"]:
        top_source = emo_analysis["source_scores"][0]
        source_labels = {
            "工作": "工作压力",
            "关系": "人际关系",
            "金钱": "金钱焦虑",
            "健康": "身心健康",
            "自我": "自我内耗",
        }
        label = source_labels.get(top_source[0], top_source[0])

        # 第二来源
        if len(emo_analysis["source_scores"]) > 1:
            second = emo_analysis["source_scores"][1]
            second_label = source_labels.get(second[0], second[0])

            if top_source[1] >= 50:
                insights.append(
                    f"🔍 你以为你的负面情绪来源很分散，\n"
                    f"   实际上 {top_source[1]}% 的负面情绪来自「{label}」——\n"
                    f"   它比第二名的「{second_label}」（{second[1]}%）高出近一倍。"
                )
            else:
                insights.append(
                    f"🔍 你的负面情绪主要来自两方面：\n"
                    f"   「{label}」（{top_source[1]}%）和「{second_label}」（{second[1]}%），\n"
                    f"   两者加起来占了 {round(top_source[1] + second[1], 1)}%。"
                )
        else:
            insights.append(
                f"🔍 你的负面情绪主要围绕着「{label}」（{top_source[1]}%）展开。"
            )

    # ── 情绪正负比洞察 ──
    if emo_analysis["positive_pct"] > emo_analysis["negative_pct"]:
        insights.append(
            f"😊 好消息：你的正面情绪（{emo_analysis['positive_pct']}%）"
            f"多于负面情绪（{emo_analysis['negative_pct']}%），"
            f"整体心态还算健康。"
        )
    elif emo_analysis["negative_pct"] > emo_analysis["positive_pct"] + 20:
        insights.append(
            f"⚠️ 注意：你的负面情绪占比高达 {emo_analysis['negative_pct']}%，"
            f"正面情绪只有 {emo_analysis['positive_pct']}%。"
            f"你最近可能过得不轻松。"
        )

    # ── 情绪趋势 ──
    if emo_analysis["trend"] == "上升":
        insights.append(
            f"📈 情绪强度呈上升趋势——你正在变得更强烈地感受情绪。"
            f"这可能意味着压力在累积，也可能意味着你越来越愿意表达真实感受。"
        )
    elif emo_analysis["trend"] == "下降":
        insights.append(
            f"📉 情绪强度在下降——你似乎正在平静下来，或者开始了钝感力模式。"
        )

    # ── 消费与情绪关联 ──
    if spend_analysis and spend_analysis["impulsive_pct"] > 30:
        insights.append(
            f"💰 你的消费中 {spend_analysis['impulsive_pct']}% 属于冲动消费"
            + ("（强度≥7）。情绪消费的迹象明显。" if correlations and any("冲动消费" in c for c in correlations) else "。")
        )

    # ── 关系洞察 ──
    if rel_analysis:
        if rel_analysis["negative_pct"] > 60:
            insights.append(
                f"🤝 关系记录中负面事件占 {rel_analysis['negative_pct']}%，"
                f"人际关系最近可能是你的消耗源之一。"
            )
        elif rel_analysis["positive_pct"] > 60:
            insights.append(
                f"🤝 关系记录中正面事件占 {rel_analysis['positive_pct']}%，"
                f"人际关系给你带来了不少能量。"
            )

    # ── 综合洞察 ──
    if correlations:
        for c in correlations[:2]:
            insights.append(f"🔄 {c}")

    # ── 收尾 ──
    if len(insights) >= 2:
        insights.append(
            f"\n💡 以上洞察基于你过去 {len(obs)} 条记录。"
            f"记录的越多，洞察越准。继续观察自己，你会看到更多。"
        )

    return insights


# ── 报告输出 ──────────────────────────────────────────────────────

def print_report(days=30):
    obs = load_observations(days)
    if not obs:
        print(f"\n{'=' * 55}")
        print(f"  人生观察员 — 报告 (过去 {days} 天)")
        print(f"{'=' * 55}")
        print()
        print("  📭 暂无数据。")
        print()
        print("  开始记录：")
        print(f"    python3 observe.py 记录 \"今天心情怎么样？\" --category emotion")
        print(f"    python3 observe.py 记录 \"买了一杯奶茶\" --category spend")
        print()
        return

    emo = analyze_emotions(obs)
    spend = analyze_spending(obs)
    rel = analyze_relationships(obs)
    correlations = analyze_correlations(obs)

    report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(obs)

    print(f"\n{'=' * 55}")
    print(f"  🧐 人生观察员 — 报告")
    print(f"  📅 {report_date}  |  过去 {days} 天  |  {total} 条记录")
    print(f"{'=' * 55}")

    # ── 1. 数据概览 ──
    print(f"\n  📊 一、数据概览")
    print(f"  {'─' * 50}")
    cat_counts = Counter(o["category"] for o in obs)
    for cat_key, (cat_label, icon) in sorted(CATEGORIES.items(),
                                              key=lambda x: cat_counts.get(x[0], 0),
                                              reverse=True):
        c = cat_counts.get(cat_key, 0)
        if c > 0:
            bar = "█" * max(1, c) + "░" * max(0, 30 - max(1, c))
            pct = c / total * 100
            print(f"  {icon} {cat_label:6s}  {bar}  {c}条 ({pct:.1f}%)")
    print(f"  {'─' * 50}")

    # ── 2. 情绪分析 ──
    if emo:
        print(f"\n  😊 二、情绪分析")
        print(f"  {'─' * 50}")
        print(f"  总记录: {emo['total']} 条  |  平均强度: {emo['avg_intensity']}/10")
        print(f"  正向: {emo['positive_pct']}%  |  负向: {emo['negative_pct']}%  |  中性: {round(emo['neutral']/emo['total']*100,1) if emo['total'] else 0}%")
        print(f"  趋势: {emo['trend']}")

        if emo["source_scores"]:
            print(f"\n  📍 情绪来源推测:")
            for source, pct in emo["source_scores"]:
                bar = "█" * max(1, int(pct / 5)) + "░" * max(0, 20 - max(1, int(pct / 5)))
                print(f"    {source:6s}  {bar}  {pct}%")

        if emo["top_tags"]:
            print(f"\n  🏷️  高频情绪标签:")
            print(f"    {'  '.join(f'#{t}({c})' for t, c in emo['top_tags'])}")

    # ── 3. 消费分析 ──
    if spend:
        print(f"\n  💰 三、消费分析")
        print(f"  {'─' * 50}")
        print(f"  记录: {spend['total']} 条  |  平均强度: {spend['avg_intensity']}/10")
        print(f"  冲动消费: {spend['impulsive']} 次 ({spend['impulsive_pct']}%)")
        if spend["top_tags"]:
            tags_str = ", ".join(f"#{t}({c})" for t, c in spend["top_tags"])
            print(f"  高频标签: {tags_str}")

    # ── 4. 关系分析 ──
    if rel:
        print(f"\n  🤝 四、人际关系")
        print(f"  {'─' * 50}")
        print(f"  记录: {rel['total']} 条")
        print(f"  正面: {rel['positive_pct']}%  |  负面: {rel['negative_pct']}%")
        if rel["top_tags"]:
            tags_str = ", ".join(f"#{t}({c})" for t, c in rel["top_tags"])
            print(f"  高频标签: {tags_str}")

    # ── 5. 核心洞察 ──
    print(f"\n  🔍 五、核心洞察")
    print(f"  {'─' * 50}")
    insights = generate_insight(obs, emo, spend, rel, correlations)
    for ins in insights:
        print(f"  {ins}")
        print()

    print(f"  {'=' * 55}")
    print()


def print_trend(days=60):
    """趋势分析：按周查看变化"""
    obs = load_observations(days)
    if not obs:
        print("📭 暂无数据")
        return

    # 按周分组
    weekly = defaultdict(lambda: {"total": 0, "emotion": 0, "spend": 0,
                                   "relationship": 0, "avg_intensity": 0,
                                   "intensities": []})
    for o in obs:
        ts = datetime.fromisoformat(o["timestamp"])
        week_start = ts - timedelta(days=ts.weekday())
        week_key = week_start.strftime("%m-%d")
        weekly[week_key]["total"] += 1
        weekly[week_key][o["category"]] = weekly[week_key].get(o["category"], 0) + 1
        weekly[week_key]["intensities"].append(o["intensity"])

    print(f"\n📈 趋势分析 — 过去 {days} 天")
    print("=" * 60)
    weeks = sorted(weekly.keys())
    for wk in weeks:
        w = weekly[wk]
        avg_i = round(sum(w["intensities"]) / len(w["intensities"]), 1) if w["intensities"] else 0
        bar = "█" * min(w["total"], 30)
        print(f"  {wk}  {bar}  {w['total']}条  (强度{avg_i}/10)")
        details = []
        if w.get("emotion"):
            details.append(f"情绪{w['emotion']}")
        if w.get("spend"):
            details.append(f"消费{w['spend']}")
        if w.get("relationship"):
            details.append(f"关系{w['relationship']}")
        if details:
            print(f"       {' | '.join(details)}")
    print()


def print_quick_insight(days=30):
    """快速洞察：只输出核心洞察"""
    obs = load_observations(days)
    if not obs:
        print("📭 暂无数据，继续记录吧。")
        return

    emo = analyze_emotions(obs)
    spend = analyze_spending(obs)
    rel = analyze_relationships(obs)
    correlations = analyze_correlations(obs)
    insights = generate_insight(obs, emo, spend, rel, correlations)

    print(f"\n💡 人生洞察 ({datetime.now().strftime('%m-%d')}, {len(obs)}条记录)")
    print("=" * 50)
    for ins in insights:
        print(f"  {ins}")
        print()
    print("=" * 50)
    print()


# ── CLI ───────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("人生观察员 — 报告模块")
        print()
        print("用法:")
        print("  report.py <天数>      # 生成完整报告，默认30")
        print("  report.py 趋势          # 趋势分析（过去60天）")
        print("  report.py 洞察          # 核心洞察摘要")
        print()
        print("示例:")
        print("  python3 report.py 30")
        print("  python3 report.py 7")
        print("  python3 report.py 趋势")
        print("  python3 report.py 洞察")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "趋势":
        print_trend()
    elif cmd == "洞察":
        print_quick_insight()
    elif cmd.isdigit():
        print_report(int(cmd))
    elif cmd == "帮助":
        print("人生观察员 — 报告模块")
        print("  report.py 30      → 30天完整报告")
        print("  report.py 7       → 7天周报")
        print("  report.py 趋势    → 趋势分析")
        print("  report.py 洞察    → 核心洞察摘要")
    else:
        print(f"❌ 未知命令: {cmd}")
        print("可用: <天数>, 趋势, 洞察")
        sys.exit(1)


if __name__ == "__main__":
    main()