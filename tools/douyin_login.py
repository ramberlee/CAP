"""抖音登录 - 手动运行此脚本保存 Cookie"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
cookie_file = "db/douyin_cookies.json"

Path("db").mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge")
    context = browser.new_context()
    page = context.new_page()
    page.goto(UPLOAD_URL)

    print("\n正在打开抖音创作者平台...")
    print("请在浏览器中完成登录（扫码/手机号均可）")
    input("\n登录成功后按 Enter 保存 Cookie...")

    # Save cookies
    cookies = context.cookies()
    Path(cookie_file).write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    print(f"Cookie 保存成功! 共 {len(cookies)} 条 -> {cookie_file}")

    # Quick check: did we land on the upload page?
    page.goto(UPLOAD_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    current_url = page.url.lower()
    if "creator" in current_url and "upload" in current_url:
        print("验证通过: 已登录状态 ✓")
    elif "login" in current_url or "passport" in current_url:
        print("⚠️  警告: 似乎未登录成功（仍在登录页），请重试")
    else:
        print(f"当前页面: {page.url[:80]}...")
        print("如发布时遇到问题请重新运行本脚本")

    browser.close()
