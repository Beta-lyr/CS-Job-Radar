"""子进程脚本：用 Playwright sync API 抓取 URL 的 HTML。
用法:
  python _playwright_fetch.py <url>                 # 单个 URL，输出 HTML
  python _playwright_fetch.py --batch <url1> <url2>  # 批量，输出 JSON {url: html}
"""

import json
import sys

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def fetch_one(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            return page.content()
        finally:
            page.close()
            browser.close()


def fetch_batch(urls: list[str]) -> dict[str, str]:
    from playwright.sync_api import sync_playwright

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for url in urls:
                page = browser.new_page()
                try:
                    page.set_viewport_size({"width": 1920, "height": 1080})
                    page.set_extra_http_headers({"User-Agent": USER_AGENT})
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(1500)
                    results[url] = page.content()
                except Exception as e:
                    results[url] = ""
                finally:
                    page.close()
        finally:
            browser.close()
    return results


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    if sys.argv[1] == "--batch":
        urls = sys.argv[2:]
        if not urls:
            sys.exit(1)
        results = fetch_batch(urls)
        sys.stdout.buffer.write(json.dumps(results, ensure_ascii=False).encode("utf-8"))
    else:
        html = fetch_one(sys.argv[1])
        sys.stdout.buffer.write(html.encode("utf-8"))


if __name__ == "__main__":
    main()
