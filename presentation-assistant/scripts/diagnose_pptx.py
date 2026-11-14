#!/usr/bin/env python3
"""Read-only structural diagnosis for an existing PowerPoint file."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    print(json.dumps({"status": "fail", "errors": ["缺少 python-pptx，无法读取 PPTX。"]}, ensure_ascii=False, indent=2))
    sys.exit(2)


def walk_text(shape):
    if getattr(shape, "has_text_frame", False):
        yield shape.text or "", shape
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                yield cell.text or "", cell
    if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
        for child in shape.shapes:
            yield from walk_text(child)


def owner_sizes(owner):
    if not getattr(owner, "has_text_frame", True) and not hasattr(owner, "text_frame"):
        return []
    try:
        paragraphs = owner.text_frame.paragraphs
    except AttributeError:
        return []
    return [round(run.font.size.pt, 2) for paragraph in paragraphs for run in paragraph.runs if run.font.size is not None]


def parse_args():
    parser = argparse.ArgumentParser(description="对既有 PPTX 做只读结构诊断。")
    parser.add_argument("pptx", help="待诊断 PPTX")
    parser.add_argument("--dense-chars", type=int, default=360, help="单页文字达到此值时提示信息密度，默认 360")
    parser.add_argument("--min-font-size", type=float, default=10.0, help="低于此字号提示可读性风险，默认 10pt")
    parser.add_argument("--aesthetic", action="store_true", help="额外输出仅供目视复核的版式结构信号，不代表审美结论")
    parser.add_argument("--report", help="JSON 报告输出路径")
    return parser.parse_args()


def emit(report, path):
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    return 1 if report["status"] == "fail" else 0


def main():
    args = parse_args()
    file = Path(args.pptx)
    if not file.is_file():
        return emit({"status": "fail", "errors": ["找不到 PPTX 文件。"]}, args.report)
    try:
        with zipfile.ZipFile(file) as archive:
            bad = archive.testzip()
            if bad:
                return emit({"status": "fail", "errors": [f"ZIP CRC 校验失败：{bad}"]}, args.report)
        deck = Presentation(file)
    except Exception as exc:
        return emit({"status": "fail", "errors": [f"无法读取 PPTX：{exc}"]}, args.report)

    pages = []
    long_blocks = defaultdict(list)
    for index, slide in enumerate(deck.slides, 1):
        blocks, fonts, pictures, tables, shape_count = [], [], 0, 0, 0
        for shape in slide.shapes:
            shape_count += 1
            if getattr(shape, "has_table", False):
                tables += 1
            if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE:
                pictures += 1
            for text, owner in walk_text(shape):
                normalized = " ".join(text.split())
                if normalized:
                    blocks.append(normalized)
                    if len(normalized) >= 24:
                        long_blocks[normalized].append(index)
                fonts.extend(owner_sizes(owner))
        chars = sum(len(item) for item in blocks)
        signals = []
        if chars >= args.dense_chars:
            signals.append({"priority": "建议优化", "type": "信息密度", "detail": f"可提取文字约 {chars} 字；检查是否可拆分、归纳或转为图表。"})
        if fonts and min(fonts) < args.min_font_size:
            signals.append({"priority": "建议优化", "type": "可读性", "detail": f"最小显式字号 {min(fonts)}pt；请在目标软件或投影环境确认。"})
        if not blocks:
            signals.append({"priority": "需要目视确认", "type": "纯视觉页", "detail": "未提取到文字；这不表示页面有问题，需要检查图片、图表或动画。"})
        if args.aesthetic:
            if shape_count >= 20:
                signals.append({"priority": "需要目视确认", "type": "版式复杂度", "detail": f"本页含 {shape_count} 个顶层对象；请目视判断是否存在不必要装饰、对齐噪音或阅读路径混乱。"})
            if len(blocks) >= 10 and chars >= 220:
                signals.append({"priority": "需要目视确认", "type": "信息层级", "detail": f"本页有 {len(blocks)} 个文字块、约 {chars} 字；请检查是否应删减、合并或换为更匹配的页型。"})
            if chars >= 100 and fonts and len(set(fonts)) <= 1:
                signals.append({"priority": "需要目视确认", "type": "层级对比", "detail": "可提取文字只出现一种显式字号；请确认标题、重点和支撑信息是否在真实页面中有足够层级。"})
        pages.append({"slide": index, "text_characters": chars, "text_blocks": len(blocks), "shapes": shape_count, "tables": tables, "pictures": pictures, "signals": signals})

    cross_page = []
    for text, slide_numbers in long_blocks.items():
        unique = sorted(set(slide_numbers))
        if len(unique) > 1:
            cross_page.append({"priority": "建议优化", "type": "跨页重复", "slides": unique, "text": text[:120], "action": "确认是否为必要页脚/定义；否则合并或改写。"})

    report = {
        "status": "pass",
        "file": str(file),
        "slides": len(deck.slides),
        "pages": pages,
        "cross_page_signals": cross_page,
        "next_step": "这是只读诊断。请由使用者选择“只保留诊断”或明确授权修订哪些页。",
        "limitations": [
            "未验证 WPS/PowerPoint 渲染、动画、图片内文字、图表含义、母版或业务事实。",
            "文字密度和字号只是信号，不自动等同于页面错误。",
            "启用 --aesthetic 后的对象数量与层级提示也只用于目视复核，不能替代真实页面审美判断。",
        ],
    }
    return emit(report, args.report)


if __name__ == "__main__":
    sys.exit(main())

