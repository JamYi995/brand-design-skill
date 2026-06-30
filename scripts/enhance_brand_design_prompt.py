#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import quote, urlparse

DEFAULT_API_BASE = "https://api.jamboxclaw.com"
ENDPOINT_PATH = "/api/brand-design-enhancer/enhance"
API_DOMAIN_ENDPOINT_PATH = "/brand-design-enhancer/enhance"
AUTH_SESSIONS_PATH = "/api/brand-design-enhancer/auth/sessions"
API_DOMAIN_AUTH_SESSIONS_PATH = "/brand-design-enhancer/auth/sessions"
DEFAULT_CONFIG_PATH = "~/.jambox/brand-design-skill.json"


class EnhancerError(Exception):
    pass


def normalize_api_base(value):
    return str(value or DEFAULT_API_BASE).strip().rstrip("/")


def endpoint_url(api_base):
    base = normalize_api_base(api_base)
    host = urlparse(base).netloc.lower()
    path = API_DOMAIN_ENDPOINT_PATH if host == "api.jamboxclaw.com" else ENDPOINT_PATH
    return f"{base}{path}"


def auth_sessions_url(api_base):
    base = normalize_api_base(api_base)
    host = urlparse(base).netloc.lower()
    path = API_DOMAIN_AUTH_SESSIONS_PATH if host == "api.jamboxclaw.com" else AUTH_SESSIONS_PATH
    return f"{base}{path}"


def auth_token_url(api_base, device_code):
    return f"{auth_sessions_url(api_base)}/{quote(str(device_code), safe='')}/token"


def resolve_config_path(value=None):
    return Path(value or os.environ.get("JAMBOX_BRAND_DESIGN_CONFIG") or DEFAULT_CONFIG_PATH).expanduser()


def load_stored_token(config_path=None):
    path = resolve_config_path(config_path)
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("token") or "").strip()
    except Exception:
        return ""


def store_token(token, config_path=None):
    value = str(token or "").strip()
    if not value:
        return
    path = resolve_config_path(config_path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps({"token": value}, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


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


def request_json(url, payload=None, headers=None, timeout=90):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="GET" if payload is None else "POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(headers or {}),
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


def start_auth_session(api_base, client_name, timeout):
    result = request_json(
        auth_sessions_url(api_base),
        {"client_name": client_name},
        timeout=timeout,
    )
    if not result.get("success"):
        raise EnhancerError(result.get("message") or result.get("code") or "创建授权链接失败。")
    return result.get("data") or {}


def poll_auth_session_token(api_base, device_code, interval, expires_in, timeout):
    deadline = time.time() + max(60, int(expires_in or 600)) + 10
    while time.time() < deadline:
        result = request_json(auth_token_url(api_base, device_code), {}, timeout=timeout)
        data = result.get("data") or {}
        status = data.get("status")
        token = str(data.get("token") or "").strip()
        if status == "authorized" and token:
            return token
        if status in {"expired", "consumed"}:
            raise EnhancerError("授权链接已失效，请重新运行命令生成新的授权链接。")
        time.sleep(max(1, int(interval or 3)))
    raise EnhancerError("等待授权超时，请重新运行命令生成新的授权链接。")


def authorize_interactively(args):
    session = start_auth_session(args.api_base, args.client_name, args.timeout)
    authorize_url = session.get("authorizeUrl") or session.get("authorize_url")
    device_code = session.get("deviceCode") or session.get("device_code")
    if not authorize_url or not device_code:
        raise EnhancerError("果酱盒子没有返回有效授权链接。")

    print("请在浏览器完成果酱盒子授权：", file=sys.stderr)
    print(authorize_url, file=sys.stderr)
    if not args.no_browser:
        try:
            webbrowser.open(authorize_url)
        except Exception:
            pass
    print("授权完成后 Agent 会自动继续。", file=sys.stderr)
    token = poll_auth_session_token(
        args.api_base,
        device_code,
        session.get("interval") or 3,
        session.get("expiresIn") or session.get("expires_in") or 600,
        args.timeout,
    )
    store_token(token, args.config)
    return token


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
    parser.add_argument("--client-name", default=os.environ.get("JAMBOX_BRAND_DESIGN_CLIENT_NAME", "Brand Design Skill"))
    parser.add_argument("--config", default=os.environ.get("JAMBOX_BRAND_DESIGN_CONFIG", DEFAULT_CONFIG_PATH))
    parser.add_argument("--no-browser", action="store_true", help="Print the authorization link without opening a browser.")
    parser.add_argument("--auth-only", action="store_true", help="Authorize and save the JamBox token, then exit.")
    args = parser.parse_args()

    args.prompt = read_prompt(args)
    if not args.prompt and not args.auth_only:
        print("请输入要增强的原始设计提示词。", file=sys.stderr)
        return 2

    token = os.environ.get("JAMBOX_BRAND_DESIGN_TOKEN", "").strip() or load_stored_token(args.config)
    if not token:
        try:
            token = authorize_interactively(args)
        except EnhancerError as error:
            print(str(error), file=sys.stderr)
            return 1
    if args.auth_only:
        print("品牌设计增强器授权已保存。")
        return 0

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
