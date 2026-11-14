#!/usr/bin/env python3
"""Static, read-only preflight for a PPTX deliverable.

This script verifies the package and extractable slide content. It deliberately
does not claim to validate WPS/PowerPoint rendering or business correctness.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    print(
        json.dumps(
            {
                "status": "fail",
                "errors": ["缺少 python-pptx，无法执行 PPTX 内容预检。"],
                "next_step": "在已获授权的环境安装 python-pptx，或改用目标软件手工验收。",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    sys.exit(2)


DEFAULT_FORBIDDEN = ("虚构测试", "技能版本", "生成过程", "TODO", "待填", "Lorem ipsum")


def add_issue(bucket: list[dict], level: str, code: str, message: str, **detail: object) -> None:
    item = {"level": level, "code": code, "message": message}
    item.update(detail)
    bucket.append(item)


def iter_shape_text(shape):
    if getattr(shape, "has_text_frame", False):
        yield shape.text or "", shape
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                yield cell.text or "", cell
    if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
        for child in shape.shapes:
            yield from iter_shape_text(child)


def font_sizes(shape) -> list[float]:
    sizes: list[float] = []
    if not getattr(shape, "has_text_frame", False):
        return sizes
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            if run.font.size is not None:
                sizes.append(round(run.font.size.pt, 2))
    return sizes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="对 PPTX 成稿进行只读静态预检。")
    parser.add_argument("pptx", help="待检查的 .pptx 文件")
    parser.add_argument("--expected-slides", type=int, help="预期页数；不一致时为失败")
    parser.add_argument("--must-contain", action="append", default=[], help="必须出现的文字，可重复使用")
    parser.add_argument("--forbid", action="append", default=[], help="不得出现的文字，可重复使用")
    parser.add_argument("--min-font-size", type=float, default=10.0, help="低于此字号时提示警告，默认 10pt")
    parser.add_argument("--report", help="将 JSON 报告另存到此路径")
    parser.add_argument("--strict", action="store_true", help="将警告视为失败")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pptx_path = Path(args.pptx).expanduser()
    issues: list[dict] = []
    metrics: dict[str, object] = {"file": str(pptx_path)}

    if not pptx_path.is_file():
        add_issue(issues, "error", "file_missing", "找不到指定 PPTX 文件。")
        return emit({"status": "fail", "metrics": metrics, "issues": issues}, args.report)
    if pptx_path.suffix.lower() != ".pptx":
        add_issue(issues, "error", "not_pptx", "文件扩展名不是 .pptx。")
        return emit({"status": "fail", "metrics": metrics, "issues": issues}, args.report)

    try:
        with zipfile.ZipFile(pptx_path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                add_issue(issues, "error", "zip_crc", "ZIP CRC 校验失败。", member=bad_member)
            metrics["zip_members"] = len(archive.infolist())
    except (OSError, zipfile.BadZipFile) as exc:
        add_issue(issues, "error", "zip_unreadable", "PPTX 压缩包无法读取。", detail=str(exc))
        return emit({"status": "fail", "metrics": metrics, "issues": issues}, args.report)

    if any(item["level"] == "error" for item in issues):
        return emit({"status": "fail", "metrics": metrics, "issues": issues}, args.report)

    try:
        presentation = Presentation(pptx_path)
    except Exception as exc:  # python-pptx uses several underlying exceptions.
        add_issue(issues, "error", "pptx_unreadable", "python-pptx 无法打开此演示文稿。", detail=str(exc))
        return emit({"status": "fail", "metrics": metrics, "issues": issues}, args.report)

    slide_count = len(presentation.slides)
    ratio = presentation.slide_width / presentation.slide_height if presentation.slide_height else 0
    metrics.update({"slides": slide_count, "aspect_ratio": round(ratio, 4)})
    if args.expected_slides is not None and slide_count != args.expected_slides:
        add_issue(issues, "error", "slide_count", "页数与预期不一致。", expected=args.expected_slides, actual=slide_count)
    if abs(ratio - (16 / 9)) > 0.03:
        add_issue(issues, "warning", "aspect_ratio", "页面不是常见的 16:9；请确认这符合模板或交付要求。", actual=round(ratio, 4))

    shape_count = text_shape_count = table_count = picture_count = 0
    all_text: list[str] = []
    long_blocks: defaultdict[str, list[int]] = defaultdict(list)
    sizes: list[float] = []
    small_font_samples: list[dict] = []
    blank_slides: list[int] = []
    for number, slide in enumerate(presentation.slides, start=1):
        slide_text: list[str] = []
        for shape in slide.shapes:
            shape_count += 1
            if getattr(shape, "has_text_frame", False):
                text_shape_count += 1
            if getattr(shape, "has_table", False):
                table_count += 1
            if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE:
                picture_count += 1
            for text, _owner in iter_shape_text(shape):
                normalized = " ".join(text.split())
                owner_sizes = font_sizes(_owner)
                sizes.extend(owner_sizes)
                for size in owner_sizes:
                    if size < args.min_font_size and len(small_font_samples) < 8:
                        small_font_samples.append(
                            {"slide": number, "size_pt": size, "text": normalized[:80]}
                        )
                if normalized:
                    slide_text.append(normalized)
                    all_text.append(normalized)
                    if len(normalized) >= 24:
                        long_blocks[normalized].append(number)
        if not slide_text:
            blank_slides.append(number)

    metrics.update(
        {
            "shapes": shape_count,
            "text_shapes": text_shape_count,
            "tables": table_count,
            "pictures": picture_count,
            "text_blocks": len(all_text),
            "font_size_pt": {"min": min(sizes) if sizes else None, "max": max(sizes) if sizes else None},
        }
    )
    if blank_slides:
        add_issue(issues, "warning", "blank_slides", "发现没有可提取文字的页面；请确认是否为预期的纯视觉页。", slides=blank_slides)
    if sizes and min(sizes) < args.min_font_size:
        add_issue(
            issues,
            "warning",
            "small_font",
            "发现低于字号阈值的文字；请检查投影可读性。",
            minimum=min(sizes),
            threshold=args.min_font_size,
            samples=small_font_samples,
        )
    if not sizes:
        add_issue(issues, "warning", "font_unavailable", "未能从文本 run 提取字号；可能是纯图片页、图表或未显式设置字号。")

    joined = "\n".join(all_text)
    for phrase in args.must_contain:
        if phrase not in joined:
            add_issue(issues, "error", "missing_required_text", "未找到要求出现的文字。", phrase=phrase)
    forbidden = list(DEFAULT_FORBIDDEN) + list(args.forbid)
    for phrase in dict.fromkeys(forbidden):
        if phrase and phrase.casefold() in joined.casefold():
            add_issue(issues, "error", "forbidden_text", "发现不应出现在正式成稿中的文字。", phrase=phrase)

    repeats = [{"text": text, "slides": slide_numbers} for text, slide_numbers in long_blocks.items() if len(set(slide_numbers)) > 1]
    if repeats:
        add_issue(issues, "warning", "repeated_long_text", "发现跨页重复的较长文本；请人工确认是否为必要说明。", samples=repeats[:5])

    errors = [issue for issue in issues if issue["level"] == "error"]
    warnings = [issue for issue in issues if issue["level"] == "warning"]
    status = "fail" if errors or (args.strict and warnings) else ("warn" if warnings else "pass")
    report = {
        "status": status,
        "metrics": metrics,
        "issues": issues,
        "limitations": [
            "这是静态预检，未验证 WPS/PowerPoint 实际渲染、动画、投影可读性或业务事实。",
            "建议在目标软件中打开成稿，必要时按 wps-acceptance.md 完成最小编辑验收。",
        ],
    }
    return emit(report, args.report)


def emit(report: dict, report_path: str | None) -> int:
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if report_path:
        target = Path(report_path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload + "\n", encoding="utf-8")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())

