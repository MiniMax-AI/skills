#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创意课堂时间可行性检测工具
输入教学环节列表，检测时间分配是否合理
用法: python time-checker.py --file segments.json
"""
import sys, json

# 各环节类型建议占比
BENCHMARK = {
    "导入": (0.05, 0.10),
    "新授": (0.25, 0.40),
    "活动": (0.20, 0.35),
    "练习": (0.10, 0.20),
    "总结": (0.05, 0.10),
    "过渡": (0.02, 0.05),
}

def check_time(total_minutes, segments):
    used = sum(s.get("minutes", 0) for s in segments)
    issues = []
    details = []
    rhythm = []

    for s in segments:
        name = s.get("name", "")
        mins = s.get("minutes", 0)
        ratio = round(mins / total_minutes * 100, 1) if total_minutes else 0

        matched = False
        for cat, (lo, hi) in BENCHMARK.items():
            if cat in name:
                expected_lo = round(lo * total_minutes)
                expected_hi = round(hi * total_minutes)
                status = "ok" if lo * total_minutes <= mins <= hi * total_minutes else "warn"
                if status == "warn":
                    msg = f"「{name}」{mins}分（基准{expected_lo}-{expected_hi}分）"
                    if mins < lo * total_minutes:
                        msg += "，偏短，建议增加"
                        issues.append(msg)
                    else:
                        msg += "，偏长，建议压缩"
                        issues.append(msg)
                matched = True
                details.append({"name": name, "minutes": mins, "ratio": ratio, "status": status})
                break

        if not matched:
            details.append({"name": name, "minutes": mins, "ratio": ratio, "status": "ok"})

        # 节奏标记
        if ratio >= 25:
            rhythm.append("SLOW")
        elif ratio >= 10:
            rhythm.append("MID")
        else:
            rhythm.append("FAST")

    remaining = total_minutes - used
    score = 100 - len(issues) * 15
    score = max(0, score)

    return {
        "summary": {
            "total_minutes": total_minutes,
            "used_minutes": used,
            "remaining": remaining,
            "usage_rate": round(used / total_minutes * 100) if total_minutes else 0
        },
        "rhythm": " → ".join(rhythm),
        "details": details,
        "score": score,
        "issues": issues,
        "suggestions": [
            "导入3-5分钟为宜，过长会影响核心环节" if any("导入" in d["name"] and d["minutes"] > 6 for d in details) else "",
            "核心新授/活动环节总占比建议≥60%" if sum(d["minutes"] for d in details if "活动" in d["name"] or "新授" in d["name"] or "精讲" in d["name"]) / total_minutes < 0.6 else "",
        ] if issues else []
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--file':
        data = json.load(open(sys.argv[2], 'r', encoding='utf-8'))
    else:
        data = json.load(sys.stdin)
    report = check_time(data.get("total_minutes", 40), data.get("segments", []))
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
