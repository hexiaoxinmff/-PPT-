---
name: presentation-assistant
description: Create, revise, diagnose, and quality-check editable presentations from natural-language requests and uploaded materials. Use for business plans, activity proposals, work reports, external proposals, and existing PPT improvement.
---

# Presentation Assistant v2.2

Turn a colleague's plain-language request and available files into a useful presentation workflow. Prioritize user-provided facts, templates, and constraints. Do not invent data, approvals, resources, or business outcomes.

## Start from the task, not a prompt form

Colleagues may speak naturally or upload files. Determine the intended deliverable, audience, available material, and constraints. Use `references/prompt-routing.md` and `references/prompt-library.md` to select and compile an internal execution prompt. Show the copyable prompt only if the user asks for it.

For contracts, money, payments, external communications, personal data, or safety, limit work to extraction, organization, drafting, comparison, and clearly marked items to confirm. Do not make legal, financial, safety, or approval decisions.

## Build the right kind of deck

Choose the deck mode in `references/delivery-modes.md` and the associated page sequence in `references/mode-page-recipes.md`. When the user asks for an outline first or key facts would change the story, follow `references/outline-first.md`; otherwise create directly when the task is sufficiently clear.

Use the user's template when provided. Without one, establish a restrained visual direction with `references/visual-craft.md`, map information relationships using `references/visual-storytelling.md`, and keep all text and base shapes editable when possible.

## Diagnose and improve existing PPTs

When the user asks for diagnosis, do not edit until they authorize it. Follow `references/revision-diagnosis.md` and `references/aesthetic-judgment.md`. Use `scripts/diagnose_pptx.py <file> --aesthetic` for read-only structure signals when Python and `python-pptx` are available; those signals do not replace a rendered visual review.

For visual reasoning, retrieve relevant patterns from `references/visual-casebook.md` or use `scripts/route_visual_case.py`. Learn the decision logic, not another project's words, brand, or visuals. Add feedback only under `references/case-learning-loop.md` and only after explicit anonymized approval.

## Verify before delivery

After creating or editing a `.pptx`, run `scripts/preflight_pptx.py <file>` when Python and `python-pptx` are available. It is read-only and checks package health, extractable content, page count, aspect ratio, fonts, and specified text rules. It does not verify actual WPS/PowerPoint rendering, projection readability, animations, or business truth.

When a target application or render is available, review the rendered deck using `references/visual-review.md`; for editable deliveries, follow `references/wps-acceptance.md` where applicable. Summarize quality using `references/delivery-scorecard.md`, distinguishing checked items from unverified ones.

## Colleague entry

Use `同事使用入口.md` and `同事体验说明.md` for copyable first-run prompts. On Windows, `一键预检.cmd` accepts a dragged `.pptx` and produces a local JSON report without altering the original file.

