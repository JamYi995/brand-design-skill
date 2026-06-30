# JamBox Brand Design Enhancer API

Production base URL:

```text
https://api.jamboxclaw.com
```

Endpoint:

```text
POST /brand-design-enhancer/enhance
```

When using the main JamBox site as the base URL, use `https://jamboxclaw.com/api/brand-design-enhancer/enhance` instead.

Authentication:

```text
Authorization: Bearer <JAMBOX_BRAND_DESIGN_TOKEN>
```

Use a `jbxmodel_` Model CLI token from JamBox API settings when this skill is installed by an external Agent. The JamBox platform checks account identity, balance, per-call limits, and daily limits. A successful call consumes credits based on the configured model token cost multiplied by 2 and rounded up.

## Browser Authorization Flow

External Agents should prefer the bundled script flow instead of asking the user to copy a token manually.

1. Create an authorization session:

```text
POST /brand-design-enhancer/auth/sessions
```

2. Open the returned `authorizeUrl` in the user's browser. The user logs in or registers in JamBox, then the page automatically creates a dedicated `jbxmodel_` CLI token for this skill.

3. Poll for the token:

```text
POST /brand-design-enhancer/auth/sessions/{deviceCode}/token
```

The token is returned once, then cleared from the authorization session. Store it only in the local Agent environment or local private config.

## Request

```json
{
  "prompt": "为咖啡品牌做一张新品海报",
  "brand_context": "面向一二线城市通勤白领，中高端价格带，品牌性格克制、专业、温暖",
  "output_language": "中文",
  "categories": ["brand"],
  "knowledge_limit": 8
}
```

Fields:

- `prompt`: required raw design prompt.
- `brand_context`: optional audience, product, style, price band, channel, or brand constraints.
- `output_language`: optional output language, default `中文`.
- `categories`: optional knowledge categories to prefer.
- `knowledge_limit`: optional knowledge snippet count, default platform value is usually `8`.

## Response

```json
{
  "success": true,
  "data": {
    "id": "usage-log-id",
    "sourcePrompt": "为咖啡品牌做一张新品海报",
    "enhancedPrompt": "优化后的品牌视觉提示词...",
    "modelName": "gpt-5.5",
    "knowledgeIds": ["brand-anchor"],
    "inputTokens": 1200,
    "outputTokens": 320,
    "baseCredits": 4,
    "chargedCredits": 8,
    "balanceAfter": 992
  }
}
```

Use `data.enhancedPrompt` as the final improved prompt. `chargedCredits` is the JamBox credit charge for this call.

## Common Errors

- `UNAUTHORIZED` or `INVALID_TOKEN`: token missing, expired, or invalid.
- `INSUFFICIENT_CREDITS`: JamBox account balance or token limit is insufficient.
- `PROMPT_REQUIRED`: request did not include a prompt.
- `MODEL_CONFIG_MISSING`: JamBox admin model usage is not configured.
- `UPSTREAM_ERROR` or `EMPTY_MODEL_RESPONSE`: model provider call failed behind JamBox.

## Curl

```bash
curl -sS https://api.jamboxclaw.com/brand-design-enhancer/enhance \
  -H "Authorization: Bearer $JAMBOX_BRAND_DESIGN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "为咖啡品牌做一张新品海报",
    "brand_context": "中高端精品咖啡，面向城市通勤白领",
    "output_language": "中文"
  }'
```
