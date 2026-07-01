"""子进程脚本：用 Playwright sync API 抓取单个 URL 的 HTML，输出到 stdout。"""

import sys

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    url = sys.argv[1]

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)
            print(page.content())
        finally:
            page.close()
            browser.close()


if __name__ == "__main__":
    main()
