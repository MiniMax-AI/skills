#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学目标可观测性检测工具
输入一组教学目标，检测动词可观测性 + ABCD结构完整性 + 层级分布
用法: python objective-validator.py --file objectives.json
"""
import sys, json, re

# 可观测动词词库
OBSERVABLE_VERBS = {
    # 识记层
    "说出": "识记", "写出": "识记", "列举": "识记", "复述": "识记",
    "背诵": "识记", "回忆": "识记", "辨认": "识记", "指出": "识记",
    "标注": "识记", "画出": "识记", "圈画": "识记", "标出": "识记",
    "填写": "识记", "连线": "识记", "排序": "识记",
    # 理解层
    "解释": "理解", "说明": "理解", "描述": "理解", "概述": "理解",
    "归纳": "理解", "总结": "理解", "比较": "理解", "区分": "理解",
    "举例": "理解", "翻译": "理解", "表达": "理解", "梳理": "理解",
    "概括": "理解", "推断": "理解", "转化": "理解",
    # 应用层
    "运用": "应用", "解决": "应用", "计算": "应用", "操作": "应用",
    "演示": "应用", "制作": "应用", "设计": "应用", "使用": "应用",
    "修改": "应用", "策划": "应用",
    # 分析层
    "分析": "分析", "分解": "分析", "对比": "分析", "论证": "分析",
    "探究": "分析", "挖掘": "分析", "梳理": "分析", "剖析": "分析",
    "鉴赏": "分析", "赏析": "分析",
    # 评价层
    "评价": "评价", "评判": "评价", "鉴定": "评价", "辩护": "评价",
    "批判": "评价", "论证": "评价", "判断": "评价",
    # 创造层
    "创作": "创造", "编写": "创造", "设计": "创造", "构建": "创造",
    "提出": "创造", "规划": "创造", "开发": "创造",
    # 行为/活动类（不适用布鲁姆但有可观测性）
    "朗读": "识记", "默读": "识记", "查阅": "识记", "收集": "识记",
    "讨论": "理解", "交流": "理解", "分享": "理解", "表演": "应用",
    "角色扮演": "应用", "调查": "分析",
}

# 模糊动词（不可观测）
FUZZY_VERBS = ["理解", "了解", "掌握", "熟悉", "认识", "体会", "感受",
               "感悟", "领会", "懂得", "知道", "明白", "学会", "意识到"]

BLOOM_LEVEL = {
    "识记": 1, "理解": 2, "应用": 3, "分析": 4, "评价": 5, "创造": 6
}

def analyze_objectives(objectives):
    results = []
    pass_count = 0
    for obj in objectives:
        verbs_found = []
        bloom_levels = []
        for v, level in OBSERVABLE_VERBS.items():
            if v in obj:
                verbs_found.append((v, level))
                bloom_levels.append(BLOOM_LEVEL.get(level, 0))

        fuzzy_found = [v for v in FUZZY_VERBS if v in obj]

        # ABCD检查
        has_condition = bool(re.search(r'通过|借助|利用|根据|结合|在.*?后|阅读|观察', obj))
        has_degree = bool(re.search(r'\d+%|至少|不少于|以内|以上|左右|正确|完整|清晰', obj))
        abcd_count = sum([1, has_condition, has_degree])

        if verbs_found:
            best_verb = max(verbs_found, key=lambda x: BLOOM_LEVEL.get(x[1], 0))
            pass_count += 1
            status = "pass"
            suggestion_parts = []
            if not has_condition:
                suggestion_parts.append("建议补充行为条件（通过什么方式/借助什么工具来完成）")
            if not has_degree:
                suggestion_parts.append("建议补充表现程度（做到什么程度算达标）")
            suggestion = "；".join(suggestion_parts) if suggestion_parts else "合格"
        else:
            best_verb = (None, None)
            status = "fail"
            suggestion = "请为教学目标添加明确的行为动词，如「说出」「列举」「解释」「运用」等"
            if not has_condition:
                suggestion += "；建议补充行为条件"
            if not has_degree:
                suggestion += "；建议补充表现程度"

        results.append({
            "objective": obj,
            "status": status,
            "verbs_found": [v[0] for v in verbs_found],
            "bloom_level": best_verb[1] if best_verb[1] else "未识别",
            "fuzzy_verbs": fuzzy_found,
            "abcd": {"condition": has_condition, "degree": has_degree, "complete": abcd_count},
            "suggestion": suggestion
        })

    # 层级分布推断
    bloom_counts = {"识记": 0, "理解": 0, "应用": 0, "分析": 0, "评价": 0, "创造": 0}
    for r in results:
        if r["bloom_level"] in bloom_counts:
            bloom_counts[r["bloom_level"]] += 1

    quality = int(pass_count / len(objectives) * 100) if objectives else 0
    return {
        "summary": {"total": len(objectives), "pass": pass_count, "quality_score": quality},
        "objectives": results,
        "bloom_distribution": bloom_counts,
        "assessment": "优秀" if quality >= 80 else "良好" if quality >= 60 else "需修改"
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--file':
        data = json.load(open(sys.argv[2], 'r', encoding='utf-8'))
    else:
        data = json.load(sys.stdin)
    report = analyze_objectives(data.get('objectives', []))
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
