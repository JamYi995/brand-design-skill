---
name: brand-design-skill
description: Enhance raw brand, poster, cover, packaging, campaign, product-visual, and commercial-design prompts through the JamBox Brand Design Enhancer API. Use when the user asks to make a design prompt more professional, brand-aware, premium, commercial, or suitable for image/design generation.
---

# Brand Design Skill

Use this skill to turn a raw design prompt into a sharper commercial brand visual prompt through JamBox's hosted Brand Design Enhancer.

The skill does not contain the private commercial design master knowledge base. JamBox injects the managed knowledge base, calls the configured model, records usage, and charges the user's JamBox credits.

## Requirements

Set a JamBox token before calling the API:

```bash
export JAMBOX_BRAND_DESIGN_TOKEN="jbxmodel_..."
```

Prefer a `jbxmodel_` Model CLI token from JamBox API settings. A JamBox web JWT also works when available. Keep tokens out of files, commits, and final answers.

The default API base is `https://api.jamboxclaw.com`. Override only for local testing:

```bash
export JAMBOX_BRAND_DESIGN_API_BASE="http://localhost:3000"
```

## Quick Use

Run the bundled script:

```bash
python3 scripts/enhance_brand_design_prompt.py "为咖啡品牌做一张新品海报"
```

With brand context:

```bash
python3 scripts/enhance_brand_design_prompt.py \
  "做一张防晒霜小红书封面" \
  --brand-context "面向一二线城市通勤女性，价格带中高端，品牌性格克制、科学、可信" \
  --language "中文"
```

For full metadata including credit usage:

```bash
python3 scripts/enhance_brand_design_prompt.py "做一张香氛礼盒主图" --json
```

## Workflow

1. Ask for the raw design prompt if the user has not provided one.
2. Collect useful brand context when available: target audience, category, price band, brand personality, channel, deliverable format, required copy, and constraints.
3. Use `scripts/enhance_brand_design_prompt.py` to call `/api/brand-design-enhancer/enhance`.
4. Return the enhanced prompt as the primary answer.
5. If the API reports `INSUFFICIENT_CREDITS`, tell the user their JamBox account needs credits.
6. If no token is configured, ask the user to set `JAMBOX_BRAND_DESIGN_TOKEN` from JamBox API settings.

## Direct API Reference

Read `references/api.md` when you need request fields, response fields, error codes, or a direct `curl` example.

Never bypass JamBox by calling upstream model providers directly for this skill. Never hard-code private knowledge snippets, model credentials, or user tokens.
