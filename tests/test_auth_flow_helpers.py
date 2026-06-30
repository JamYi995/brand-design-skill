import importlib.util
import json
import os
import tempfile


spec = importlib.util.spec_from_file_location("enhancer", "scripts/enhance_brand_design_prompt.py")
enhancer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enhancer)


def test_auth_endpoint_urls():
    assert enhancer.auth_sessions_url("https://api.jamboxclaw.com") == "https://api.jamboxclaw.com/brand-design-enhancer/auth/sessions"
    assert enhancer.auth_token_url("https://api.jamboxclaw.com", "bdauth_abc") == "https://api.jamboxclaw.com/brand-design-enhancer/auth/sessions/bdauth_abc/token"
    assert enhancer.auth_sessions_url("https://jamboxclaw.com") == "https://jamboxclaw.com/api/brand-design-enhancer/auth/sessions"


def test_token_config_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "brand-design-skill.json")
        enhancer.store_token("jbxmodel_test_token", config_path)
        assert enhancer.load_stored_token(config_path) == "jbxmodel_test_token"
        with open(config_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        assert data["token"] == "jbxmodel_test_token"


if __name__ == "__main__":
    test_auth_endpoint_urls()
    test_token_config_roundtrip()
    print("brand design auth helper tests passed")
