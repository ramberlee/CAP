"""Douyin (TikTok China) publisher using Playwright browser automation."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DouyinPublisher:
    """Publishes content to Douyin via Playwright browser automation.

    Requires: Playwright installed, pre-saved login cookies.
    First run: set headless=false, login manually, cookies will be saved.
    """

    def __init__(self, config: dict):
        self.cookie_file = config.get("cookie_file", "db/douyin_cookies.json")
        self.headless = config.get("headless", False)
        self.channel = config.get("channel", "chrome")

    def _save_cookies(self, context):
        cookies = context.cookies()
        cookie_path = Path(self.cookie_file)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        cookie_path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
        logger.info(f"Cookies saved to {self.cookie_file}")

    def _load_cookies(self, context):
        cookie_path = Path(self.cookie_file)
        if cookie_path.exists():
            cookies = json.loads(cookie_path.read_text())
            context.add_cookies(cookies)
            logger.info(f"Cookies loaded from {self.cookie_file}")
            return True
        return False

    def _login_interactive(self, page, context):
        logger.info("Opening Douyin creator login page...")
        page.goto("https://creator.douyin.com/creator-micro/content/upload")
        logger.info("Please login manually in the browser window. Press Enter here when done...")
        input()
        self._save_cookies(context)

    def publish(self, content: dict) -> dict:
        """Publish content to Douyin.

        Args:
            content: dict with 'title', 'body'/'script', 'tags' keys.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {"success": False, "error": "playwright not installed. Run: pip install playwright && playwright install chromium"}

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, channel=self.channel)
                context = browser.new_context()
                page = context.new_page()

                # Try loading cookies
                if not self._load_cookies(context):
                    self._login_interactive(page, context)

                # Navigate to creator center
                page.goto("https://creator.douyin.com/creator-micro/content/upload")
                page.wait_for_load_state("networkidle")

                # Check if still logged in
                if "login" in page.url.lower():
                    self._login_interactive(page, context)
                    page.goto("https://creator.douyin.com/creator-micro/content/upload")
                    page.wait_for_load_state("networkidle")

                # Fill video description/title
                script_text = content.get("body", content.get("script", ""))
                tags_str = " ".join(content.get("tags", []))
                full_text = f"{content['title']}\n\n{script_text}\n\n{tags_str}"

                # Try to find and fill the description input
                try:
                    desc_input = page.locator('[class*="desc"] [contenteditable="true"]').first
                    if desc_input.is_visible(timeout=5000):
                        desc_input.fill(full_text)
                    else:
                        # Fallback: try other selectors
                        page.locator('[contenteditable="true"]').first.fill(full_text)
                except Exception as e:
                    logger.warning(f"Could not auto-fill description: {e}")

                logger.info(f"Content filled for Douyin: {content['title'][:30]}...")

                # Note: Video upload is not automated here
                # User needs to manually upload video and click publish
                logger.info("Please upload video and click '发布' in the browser window.")
                logger.info("Press Enter here when publishing is complete...")
                input()

                self._save_cookies(context)
                browser.close()
                return {"success": True, "message": "Published via browser automation"}

        except Exception as e:
            return {"success": False, "error": str(e)}
