#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点覆盖完整性检测工具
输入知识点清单和教学活动，检查每项知识点是否有对应活动覆盖
用法: python coverage-checker.py --file coverage.json
"""
import sys, json

def check_coverage(knowledge_points, activities):
    """
    knowledge_points: [{"id":"K01","name":"...","level":"must/should/optional"}]
    activities: [{"name":"环节名","covers":["K01","K02"]}]
    """
    must_points = [kp for kp in knowledge_points if kp.get("level") == "must"]
    all_points = {kp["id"]: kp for kp in knowledge_points}

    covered = set()
    activity_map = {}
    for act in activities:
        for kid in act.get("covers", []):
            covered.add(kid)
            if kid not in activity_map:
                activity_map[kid] = []
            activity_map[kid].append(act["name"])

    missing_must = [kp for kp in must_points if kp["id"] not in covered]
    uncovered = [kp for kp in knowledge_points if kp["id"] not in covered]

    coverage_rate = round(len(covered) / len(knowledge_points) * 100) if knowledge_points else 0
    must_coverage = round((len(must_points) - len(missing_must)) / len(must_points) * 100) if must_points else 100

    issues = []
    if missing_must:
        issues.append(f"必备知识点未覆盖：{', '.join(k['name'] for k in missing_must)}")
    if coverage_rate < 100:
        issues.append("存在知识点未被任何活动环节覆盖")

    return {
        "summary": {
            "total_points": len(knowledge_points),
            "covered": len(covered),
            "coverage_rate": coverage_rate,
            "must_coverage_rate": must_coverage,
            "score": min(100, must_coverage)
        },
        "missing_must": [k["name"] for k in missing_must],
        "uncovered_all": [k["name"] for k in uncovered],
        "activity_map": activity_map,
        "issues": issues,
        "assessment": "覆盖完整" if not issues else "覆盖不全，请补充"
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--file':
        data = json.load(open(sys.argv[2], 'r', encoding='utf-8'))
    else:
        data = json.load(sys.stdin)
    report = check_coverage(data.get("knowledge_points", []), data.get("activities", []))
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
