"""Xiaohongshu (Little Red Book) publisher using Playwright browser automation."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class XiaohongshuPublisher:
    """Publishes content to Xiaohongshu via Playwright browser automation.

    Requires: Playwright installed, pre-saved login cookies.
    First run: set headless=false, login manually, cookies will be saved.
    """

    def __init__(self, config: dict):
        self.cookie_file = config.get("cookie_file", "db/xhs_cookies.json")
        self.headless = config.get("headless", False)
        self.channel = config.get("channel", "chrome")

    def _save_cookies(self, context):
        """Save browser cookies to file."""
        cookies = context.cookies()
        cookie_path = Path(self.cookie_file)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        cookie_path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
        logger.info(f"Cookies saved to {self.cookie_file}")

    def _load_cookies(self, context):
        """Load saved cookies into browser context."""
        cookie_path = Path(self.cookie_file)
        if cookie_path.exists():
            cookies = json.loads(cookie_path.read_text())
            context.add_cookies(cookies)
            logger.info(f"Cookies loaded from {self.cookie_file}")
            return True
        return False

    def _login_interactive(self, page, context):
        """Interactive login - user scans QR code in browser."""
        logger.info("Opening Xiaohongshu login page...")
        page.goto("https://creator.xiaohongshu.com/publish/publish")
        logger.info("Please login manually in the browser window. Press Enter here when done...")
        input()
        self._save_cookies(context)

    def publish(self, content: dict) -> dict:
        """Publish a note to Xiaohongshu.

        Args:
            content: dict with 'title', 'body', 'tags' keys.
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

                # Navigate to publish page
                page.goto("https://creator.xiaohongshu.com/publish/publish")
                page.wait_for_load_state("networkidle")

                # Check if still logged in
                if "login" in page.url.lower():
                    self._login_interactive(page, context)
                    page.goto("https://creator.xiaohongshu.com/publish/publish")
                    page.wait_for_load_state("networkidle")

                # Select "图文" (image-text) mode
                # Note: Selectors may change - update as needed
                try:
                    page.click('text=上传图文', timeout=5000)
                except Exception:
                    logger.warning("Could not find '上传图文' button, trying to continue...")

                # Fill title
                title_input = page.locator('[placeholder*="标题"]').first
                if title_input.is_visible():
                    title_input.fill(content["title"])

                # Fill body content
                body_editor = page.locator('[contenteditable="true"]').first
                if body_editor.is_visible():
                    full_text = content["body"]
                    if content.get("tags"):
                        full_text += "\n\n" + " ".join(content["tags"])
                    body_editor.fill(full_text)

                logger.info(f"Content filled for Xiaohongshu: {content['title'][:30]}...")

                # Note: Image upload is not automated here
                # User needs to manually add images and click publish
                logger.info("Please add images and click '发布' in the browser window.")
                logger.info("Press Enter here when publishing is complete...")
                input()

                # Save cookies for next time
                self._save_cookies(context)

                browser.close()
                return {"success": True, "message": "Published via browser automation"}

        except Exception as e:
            return {"success": False, "error": str(e)}
