#!/usr/bin/env python3
"""Suggest a prompt-library route from a colleague's natural-language request.

The script is local and read-only. It only suggests a template; the agent must
still interpret attachments, context, and user corrections before executing.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    key: str
    title: str
    keywords: tuple[str, ...]
    caution: str
    priority: int = 0


ROUTES = (
    Route("contract-review", "05 合同条款提取与核对", ("合同", "条款", "补充协议", "续签", "版本比对"), "仅提取、比较和列待确认，不替代法律或业务审核。"),
    Route("contract-draft", "06 合同或函件草拟", ("起草合同", "合同制作", "填合同", "补充协议草拟", "起草", "草拟"), "只基于已确认资料和模板制作草稿。", 10),
    Route("reconciliation", "08 对账、费用、发票与报表核对", ("对账", "费用核对", "发票", "开票", "账单", "报销"), "不确认付款、税务或冲抵结论。"),
    Route("patrol", "09 巡检、保洁与现场问题记录", ("巡检", "保洁", "整改", "现场问题", "卫生", "照片"), "照片只能作为可见问题证据，不认定整改或安全结果。"),
    Route("operations", "10 设备、水电与运营数据汇总", ("水电", "抄表", "表号", "设备巡检", "能耗", "运营数据"), "核实周期、单位和规则后再计算。"),
    Route("vendor", "11 供应商资料与报价比较", ("供应商", "报价", "比价", "采购", "服务商"), "只做同维度比较，不替代采购决定。"),
    Route("event", "12 活动策划与执行清单", ("活动", "排期", "分工", "复盘", "执行方案"), "未确认的预算、人数和资源均标待确认。"),
    Route("ppt", "13 PPT 制作、修改与审美诊断", ("ppt", "汇报", "演示文稿", "幻灯片", "方案稿"), "根据用途选择决策、执行或对外模式。", 9),
    Route("image", "14 生图、改图与效果图需求", ("效果图", "生图", "改图", "海报", "门头", "主视觉", "图片"), "先确认精确文字、修改范围和参考图角色。"),
    Route("writing", "15 文案、方案与改写", ("文案", "改写", "润色", "方案", "公众号", "宣传"), "不补写没有依据的数据、承诺或案例。"),
    Route("research", "16 调研、资料搜集与决策建议", ("调研", "找资料", "找案例", "研究", "查一下", "搜集"), "区分可核验来源与尚未证实信息。"),
    Route("meeting", "02 会议记录 → 行动清单", ("会议纪要", "会议记录", "行动项", "开会"), "未明确的负责人和日期标待确认。"),
    Route("report", "03 周报、月报、工作汇报", ("周报", "月报", "工作汇报", "日报", "总结"), "只汇总已提供的进度和事实。"),
    Route("message", "04 通知、函件与微信沟通", ("通知", "微信", "邮件", "回复", "催办", "催缴"), "金额、期限和责任必须来自已确认资料。"),
    Route("ledger", "07 台账整理与数据清洗", ("台账", "整理表格", "合并表格", "清洗数据", "档案"), "保留原始记录，不把空白当作零。"),
    Route("extract", "01 文件阅读与信息提取", ("提取", "读文件", "识别文字", "整理资料", "扫描件"), "记录来源位置并标出无法辨认项。"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="根据自然语言建议提示词库路由。")
    parser.add_argument("--request", required=True, help="使用者原话")
    parser.add_argument("--assets", default="未说明；先判断本轮附件是内容来源、模板、原件还是参考图。", help="已上传资料的简短说明")
    args = parser.parse_args()
    request = re.sub(r"\s+", " ", args.request.strip())
    scored = []
    for route in ROUTES:
        matches = [word for word in route.keywords if word.lower() in request.lower()]
        if matches:
            scored.append((len(matches), route.priority, sum(len(word) for word in matches), route, matches))
    scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    candidates = [
        {"route": route.key, "template": route.title, "matched_terms": words, "caution": route.caution}
        for _count, _priority, _length, route, words in scored[:3]
    ]
    if not candidates:
        candidates = [{"route": "general", "template": "17 通用任务分解", "matched_terms": [], "caution": "先确认最终交付物、已有资料和关键风险。"}]
    result = {
        "request": request,
        "recommended": candidates[0],
        "alternatives": candidates[1:],
        "compiled_prompt": (
            f"请按提示词库中的《{candidates[0]['template']}》处理本任务。\n"
            f"使用者原话：{request}\n"
            f"现有资料：{args.assets}\n"
            "先确认资料角色与最终交付物；信息足够则直接完成，缺少会改变结果的信息时只问一到两个问题。\n"
            f"约束：{candidates[0]['caution']}\n"
            "输出中区分已确认事实、建议和待确认项；不得编造资料中没有的业务事实。"
        ),
        "next_step": "结合附件、上下文和使用者目标选择模板；路由结果不是自动执行或业务结论。",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

