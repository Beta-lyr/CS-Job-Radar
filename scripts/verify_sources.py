"""验证 sources.json 中的 URL 是否可访问。"""

import json
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SOURCES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "source-registry", "sources.json")
TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; CSJobRadar/1.0)"


def check_url(url: str, label: str) -> dict:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True)
        return {"url": url, "status": resp.status_code, "final_url": resp.url, "size": len(resp.text), "ok": resp.ok}
    except requests.ConnectionError:
        return {"url": url, "status": "CONNECTION_ERROR", "final_url": "", "size": 0, "ok": False}
    except requests.Timeout:
        return {"url": url, "status": "TIMEOUT", "final_url": "", "size": 0, "ok": False}
    except Exception as e:
        return {"url": url, "status": str(e)[:60], "final_url": "", "size": 0, "ok": False}


def main():
    with open(SOURCES_PATH, encoding="utf-8") as f:
        sources = json.load(f)

    print(f"Checking {len(sources)} sources...\n")

    for s in sources:
        name = s["name"]
        list_url = s["list_url"]
        enabled = s.get("enabled", True)
        tag = "[ON]" if enabled else "[OFF]"

        result = check_url(list_url, name)
        status = "OK" if result["ok"] else "FAIL"
        icon = "✓" if result["ok"] else "✗"

        print(f"{icon} {tag} {name}")
        print(f"   URL: {list_url}")
        if result.get("final_url") and result["final_url"] != list_url:
            print(f"   Redirect: {result['final_url']}")
        print(f"   HTTP {result['status']} | {result['size']} bytes")
        print()


if __name__ == "__main__":
    main()
