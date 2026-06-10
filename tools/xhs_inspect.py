"""打开小红书发布页面，手动检查元素结构"""
from playwright.sync_api import sync_playwright
import json
from pathlib import Path

p = sync_playwright().start()
browser = p.chromium.launch(headless=False, channel="msedge")
context = browser.new_context(viewport={"width": 1920, "height": 1080})
page = context.new_page()

cookie_file = "db/xhs_cookies.json"
if Path(cookie_file).exists():
    cookies = json.loads(Path(cookie_file).read_text())
    context.add_cookies(cookies)

page.goto("https://creator.xiaohongshu.com/publish/publish")
print("浏览器已打开小红书发布页面")
print("请手动检查：1.上传图片后 2.查看发布按钮结构 3.用F12检查元素")
input("完成后按 Enter 关闭浏览器...")
browser.close()
p.stop()
