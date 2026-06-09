"""抖音登录 - 手动运行此脚本保存 Cookie"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

cookie_file = "db/douyin_cookies.json"
Path("db").mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="msedge")
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://creator.douyin.com/creator-micro/content/upload")
    input("请在浏览器中登录抖音，完成后按 Enter...")
    cookies = context.cookies()
    Path(cookie_file).write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    print(f"Cookie 保存成功! 共 {len(cookies)} 条 -> {cookie_file}")
    browser.close()
