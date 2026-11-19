# PPT 制作与修改助手

把零散资料做成汇报 PPT，或者按你的模板修改旧稿。你只要说主题、给谁看、希望交付什么，助手就会选合适的页型、版式和图表。

## 第一次使用

1. [下载最新版 ZIP](https://github.com/hexiaoxinmff/-PPT-/archive/refs/heads/main.zip) 并解压。
2. 在支持自定义技能的办公平台找到导入入口，选择整个 `presentation-assistant` 文件夹。该目录里直接有 `SKILL.md`。更新时先备份旧技能和个人资料，与维护技能分开存放私人模板。
3. 打开新会话，选择或调用本技能，上传本次允许处理的资料，然后直接说你的需求。能否生成可编辑 PPTX、保留母版或播放动效，取决于当前平台工具。
4. 收到文件后，用 WPS 或 PowerPoint 打开检查。想先看目录，可以在第一句话里说「先给我大纲」。

## 可以直接复制的三句话

- 新做一份：「把这些活动资料做成一份给领导看的 8 页 PPT，突出方案和要拍板的事。」
- 改旧稿：「用我上传的 PPT 做底稿，只改第 3 页的数据和第 5 页的排期，另存一份。」
- 保存再复用：「把这份 PPT 存为我的月报模板，以后做月报自动优先匹配。封面和页脚固定，数据与图表每月替换。」

下次直接说「用这个月的表格做月报」。平台能读取私人模板库时，助手会优先找匹配的私人模板，再用内置页型补齐。平台无法跨会话读取时，可带上源文件或助手给你的模板卡。

## 附带资源

- [模板库与选用规则](presentation-assistant/references/template-library.md)
- [同事使用入口](presentation-assistant/同事使用入口.md)
- [高级制作技法](presentation-assistant/references/advanced-slide-techniques.md)与[放映动效](presentation-assistant/references/presentation-motion.md)
- [本地静态预检](presentation-assistant/references/preflight.md)依赖 Python 和 `python-pptx`，能检查 PPTX 结构与部分文字规则。放映效果以目标软件实测为准。

私人模板、原稿和公司资料请保存在你有权限的私人位置。公开仓库提供通用规则和虚构示例。
