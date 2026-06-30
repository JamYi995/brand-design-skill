#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT_API_BASE = "https://api.jamboxclaw.com"
ENDPOINT_PATH = "/api/brand-design-enhancer/enhance"
API_DOMAIN_ENDPOINT_PATH = "/brand-design-enhancer/enhance"


class EnhancerError(Exception):
    pass


def normalize_api_base(value):
    return str(value or DEFAULT_API_BASE).strip().rstrip("/")


def endpoint_url(api_base):
    base = normalize_api_base(api_base)
    host = urlparse(base).netloc.lower()
    path = API_DOMAIN_ENDPOINT_PATH if host == "api.jamboxclaw.com" else ENDPOINT_PATH
    return f"{base}{path}"


def parse_categories(values):
    categories = []
    for value in values or []:
        for item in str(value).split(","):
            item = item.strip()
            if item and item not in categories:
                categories.append(item)
    return categories


def build_payload(args):
    payload = {
        "prompt": args.prompt.strip(),
        "output_language": args.language,
    }
    if args.brand_context:
        payload["brand_context"] = args.brand_context.strip()
    categories = parse_categories(args.category)
    if categories:
        payload["categories"] = categories
    if args.knowledge_limit:
        payload["knowledge_limit"] = args.knowledge_limit
    return payload


def read_prompt(args):
    prompt = " ".join(args.prompt_parts).strip()
    if prompt:
        return prompt
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def parse_error_response(error):
    try:
        body = error.read().decode("utf-8")
        data = json.loads(body)
        return data.get("message") or data.get("code") or body
    except Exception:
        return str(error)


def call_enhancer(api_base, token, payload, timeout):
    if not token:
        raise EnhancerError("缺少 JAMBOX_BRAND_DESIGN_TOKEN，请先在环境变量中设置果酱盒子 Token。")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint_url(api_base),
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise EnhancerError(parse_error_response(error)) from error
    except urllib.error.URLError as error:
        raise EnhancerError(f"无法连接果酱盒子品牌设计增强器：{error.reason}") from error
    except json.JSONDecodeError as error:
        raise EnhancerError("果酱盒子返回了无法解析的响应。") from error


def main():
    parser = argparse.ArgumentParser(description="Enhance a brand design prompt through JamBox.")
    parser.add_argument("prompt_parts", nargs="*", help="Raw design prompt. If omitted, stdin is used.")
    parser.add_argument("--brand-context", default="", help="Audience, category, price band, style, channel, or constraints.")
    parser.add_argument("--language", default="中文", help="Output language. Default: 中文")
    parser.add_argument("--category", action="append", default=[], help="Knowledge category. Can be repeated or comma-separated.")
    parser.add_argument("--knowledge-limit", type=int, default=0, help="Optional knowledge snippet limit.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON response data.")
    parser.add_argument("--api-base", default=os.environ.get("JAMBOX_BRAND_DESIGN_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    args.prompt = read_prompt(args)
    if not args.prompt:
        print("请输入要增强的原始设计提示词。", file=sys.stderr)
        return 2

    token = os.environ.get("JAMBOX_BRAND_DESIGN_TOKEN", "").strip()
    try:
        result = call_enhancer(args.api_base, token, build_payload(args), args.timeout)
    except EnhancerError as error:
        print(str(error), file=sys.stderr)
        return 1

    if not result.get("success"):
        print(result.get("message") or result.get("code") or "品牌设计增强失败。", file=sys.stderr)
        return 1

    data = result.get("data") or {}
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    enhanced_prompt = str(data.get("enhancedPrompt") or "").strip()
    if not enhanced_prompt:
        print("品牌设计增强器没有返回增强后的提示词。", file=sys.stderr)
        return 1
    print(enhanced_prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
