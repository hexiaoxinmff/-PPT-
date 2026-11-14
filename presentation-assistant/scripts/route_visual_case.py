#!/usr/bin/env python3
"""Suggest visual casebook entries from a slide symptom and delivery mode."""

from __future__ import annotations

import argparse
import json
import re


CASES = {
    "C01": {"name": "决策页：背景堆满，决策缺席", "terms": ("决策", "领导", "背景", "重点", "结论"), "modes": ("decision",)},
    "C02": {"name": "比较页：三列卡片看似整齐，实际不可比", "terms": ("比较", "对比", "方案", "供应商", "三列"), "modes": ("decision", "external")},
    "C03": {"name": "时间页：日期散落，没有节奏", "terms": ("排期", "时间", "里程碑", "日期", "进度"), "modes": ("execution", "decision")},
    "C04": {"name": "流程页：箭头很多，责任不清", "terms": ("流程", "分工", "协作", "责任", "交接"), "modes": ("execution",)},
    "C05": {"name": "表格页：所有字段同权，关键判断被淹没", "terms": ("表格", "数据太多", "字号", "明细", "重点"), "modes": ("decision", "execution")},
    "C06": {"name": "数据页：有数字，没有结论", "terms": ("数据", "图表", "趋势", "分析", "数字"), "modes": ("decision", "external")},
    "C07": {"name": "空间页：概念图被误认为现场承诺", "terms": ("空间", "动线", "平面", "场地", "效果图"), "modes": ("decision", "external")},
    "C08": {"name": "图片页：小图拼贴很多，没有主角", "terms": ("图片", "拼贴", "照片", "主图", "焦点"), "modes": ("external",)},
    "C09": {"name": "封面：装饰很多，主题不明确", "terms": ("封面", "主题", "标题", "logo"), "modes": ("decision", "execution", "external")},
    "C10": {"name": "行动页：结尾重复前文，没有下一步", "terms": ("结尾", "下一步", "行动", "结束页", "跟进"), "modes": ("decision", "execution")},
    "C11": {"name": "执行稿：每页都是卡片墙，记忆点消失", "terms": ("卡片", "重复", "节奏", "页面", "单调"), "modes": ("execution",)},
    "C12": {"name": "对外稿：宣传语强，可信依据弱", "terms": ("招商", "宣传", "对外", "卖点", "依据"), "modes": ("external",)},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="从视觉症状推荐案例库条目。")
    parser.add_argument("--request", required=True, help="页面问题或使用者原话")
    parser.add_argument("--mode", choices=("decision", "execution", "external"), help="成稿模式，可选")
    args = parser.parse_args()
    text = re.sub(r"\s+", " ", args.request.lower())
    scored = []
    for key, case in CASES.items():
        hits = [term for term in case["terms"] if term.lower() in text]
        mode_bonus = 1 if args.mode and args.mode in case["modes"] else 0
        if hits or mode_bonus:
            scored.append((len(hits), mode_bonus, key, case, hits))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    candidates = [
        {"case_id": key, "name": case["name"], "matched_terms": hits, "modes": case["modes"]}
        for _hits, _bonus, key, case, hits in scored[:3]
    ]
    result = {
        "request": args.request,
        "mode": args.mode,
        "cases": candidates,
        "next_step": "阅读案例的取舍逻辑并结合真实页面判断；不得复制案例文案、品牌或未授权视觉素材。",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

