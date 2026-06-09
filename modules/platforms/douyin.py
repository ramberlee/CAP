"""Douyin (TikTok China) publisher using Playwright browser automation."""

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"


class DouyinPublisher:
    """Publishes content to Douyin via Playwright browser automation.

    Supports batch publishing: opens browser once, publishes all videos, then closes.
    """

    def __init__(self, config: dict):
        self.cookie_file = config.get("cookie_file", "db/douyin_cookies.json")
        self.headless = config.get("headless", False)
        self.channel = config.get("channel", "chrome")
        self.post_publish_wait = config.get("post_publish_wait", 30)

    def _save_cookies(self, context):
        cookies = context.cookies()
        cookie_path = Path(self.cookie_file)
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        cookie_path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))

    def _load_cookies(self, context):
        cookie_path = Path(self.cookie_file)
        if cookie_path.exists():
            cookies = json.loads(cookie_path.read_text())
            context.add_cookies(cookies)
            return True
        return False

    def _get_video_path(self, content: dict) -> Path | None:
        for url in content.get("media_urls", []):
            p = Path(url)
            if p.suffix == ".mp4" and p.exists():
                return p
        return None

    def _wait_for_upload(self, page, timeout: int = 120) -> bool:
        for i in range(timeout):
            time.sleep(1)
            if i % 10 == 0:
                logger.info(f"  Waiting for upload... ({i}s)")
            try:
                btn = page.get_by_role("button", name="发布", exact=True)
                if btn.is_visible(timeout=1000):
                    logger.info(f"Upload complete after {i}s")
                    return True
            except:
                pass
        logger.warning(f"Upload wait timed out after {timeout}s")
        return False

    def _clean_script(self, script_text: str) -> str:
        text = re.sub(r"【[^】]+】", "", script_text)
        text = re.sub(r"\n*---\n*", "，", text)
        return re.sub(r"\s+", " ", text).strip()

    def _publish_one(self, page, content: dict) -> dict:
        """Publish a single content item on the already-open page."""
        video_path = self._get_video_path(content)
        if not video_path:
            return {"success": False, "error": "No video file found"}

        title = content.get("title", "")
        logger.info(f"Publishing: {title[:40]}")

        # Navigate to upload page
        page.goto(UPLOAD_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Upload video
        try:
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(str(video_path))
            self._wait_for_upload(page, timeout=120)
            time.sleep(2)
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {e}"}

        # Fill description
        script_text = content.get("body", content.get("script", ""))
        tags_str = " ".join(content.get("tags", []))
        clean_script = self._clean_script(script_text)
        full_text = f"{title}\n\n{clean_script}\n\n{tags_str}".strip()

        try:
            desc_inputs = page.locator('[contenteditable="true"]')
            if desc_inputs.count() > 0:
                desc_inputs.first.fill(full_text)
                logger.info(f"  Description filled ({len(full_text)} chars)")
        except Exception as e:
            logger.warning(f"  Could not fill description: {e}")

        time.sleep(1)

        # Click publish
        try:
            publish_btn = page.get_by_role("button", name="发布", exact=True)
            publish_btn.wait_for(state="visible", timeout=10000)
            publish_btn.click()
            logger.info("  Publish button clicked!")

            # Wait for CAPTCHA/verification/redirect
            logger.info(f"  Waiting {self.post_publish_wait}s for verification/redirect...")
            page.wait_for_timeout(self.post_publish_wait * 1000)

            final_url = page.url
            if "manage" in final_url or "success" in final_url:
                logger.info(f"  Published! -> {final_url}")
            else:
                logger.info(f"  Final URL: {final_url}")

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": f"Publish click failed: {e}"}

    def publish(self, content: dict) -> dict:
        """Publish a single content item (opens/closes browser)."""
        results = self.publish_batch([content])
        return results[0] if results else {"success": False, "error": "No result"}

    def publish_batch(self, contents: list[dict]) -> list[dict]:
        """Publish multiple contents in one browser session.

        Opens browser once, publishes all videos sequentially, then closes.
        Returns list of results matching the input contents.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            err = "playwright not installed. Run: pip install playwright && playwright install chromium"
            return [{"success": False, "error": err} for _ in contents]

        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, channel=self.channel)
                context = browser.new_context()
                page = context.new_page()

                self._load_cookies(context)

                # Navigate to creator center to check login
                page.goto(UPLOAD_URL)
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                if "login" in page.url.lower():
                    logger.error("Not logged in. Run: python tools/douyin_login.py")
                    browser.close()
                    return [{"success": False, "error": "Not logged in"} for _ in contents]

                logger.info(f"Browser ready, publishing {len(contents)} items...")

                for i, content in enumerate(contents):
                    logger.info(f"\n--- [{i+1}/{len(contents)}] ---")
                    result = self._publish_one(page, content)
                    results.append(result)
                    self._save_cookies(context)

                    if result["success"]:
                        logger.info(f"  ✅ Success")
                    else:
                        logger.warning(f"  ❌ Failed: {result.get('error')}")

                browser.close()
                logger.info(f"\nBrowser closed. Results: {sum(1 for r in results if r['success'])}/{len(results)} success")

        except Exception as e:
            logger.error(f"Batch publish error: {e}")
            while len(results) < len(contents):
                results.append({"success": False, "error": str(e)})

        return results
