# 一键预检

`scripts/preflight_pptx.py` 是生成或修改 `.pptx` 后的静态预检，不读取网络、不上传文件、不改写原 PPT。

## 常用命令

```powershell
python scripts/preflight_pptx.py "C:\路径\成稿.pptx"
python scripts/preflight_pptx.py "C:\路径\成稿.pptx" --expected-slides 8 --must-contain "项目名称" --forbid "TODO" --report "C:\路径\预检报告.json"
```

Windows 同事也可以把 `.pptx` 文件直接拖到包根目录的 `一键预检.cmd` 上。它会在原 PPT 同目录生成 `文件名_preflight-report.json`，不会覆盖或改写原文件。该入口只使用本机 Python；若电脑没有 Python 或 `python-pptx`，会明确提示缺少的条件。

## 检查项目

- 文件是否存在、ZIP CRC 是否完整、PPTX 是否能被 `python-pptx` 打开。
- 页数、页面比例、文本/表格/图片对象数量、最小字号、空白页、关键文字和禁用文字。
- 重复的较长文本块只作提醒，不把页脚、标题或短文本误判为问题。

`--strict` 会把警告视为失败；只有交付标准明确要求时才使用。预检无法检查真实字体替换、文本自动换行、动画、投影效果、WPS/PowerPoint 兼容性或业务事实正确性。需要这些结论时，继续按 `wps-acceptance.md` 和人工审稿执行。

