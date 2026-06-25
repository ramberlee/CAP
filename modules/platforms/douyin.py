"""Douyin (TikTok China) publisher using Playwright browser automation."""

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"


# ---------------------------------------------------------------------------
# Content validation (rule-based)
# ---------------------------------------------------------------------------

def validate_content(result: dict, **_) -> list[str]:
    """Validate douyin script quality. Returns list of warnings (non-blocking)."""
    script = result.get("script", result.get("body", ""))
    tags = result.get("tags", [])
    warnings = []

    # Check three-part structure
    has_hook = "【钩子】" in script
    has_value = "【价值】" in script
    has_ending = "【收尾】" in script
    if not (has_hook and has_value and has_ending):
        missing = []
        if not has_hook:
            missing.append("【钩子】")
        if not has_value:
            missing.append("【价值】")
        if not has_ending:
            missing.append("【收尾】")
        warnings.append(f"缺少三段结构: {', '.join(missing)}")

    # Check separator
    if "---" not in script:
        warnings.append("缺少 --- 分隔符")

    # Check word count (200-800 chars for Chinese scripts)
    char_count = len(script)
    if char_count < 200:
        warnings.append(f"脚本过短 ({char_count}字)，建议200-800字")
    elif char_count > 800:
        warnings.append(f"脚本过长 ({char_count}字)，建议200-800字")

    # Check tags
    if len(tags) < 3:
        warnings.append(f"标签不足 ({len(tags)}个)，建议3-5个")
    elif len(tags) > 5:
        warnings.append(f"标签过多 ({len(tags)}个)，建议3-5个")

    ai_tag_found = any("AI" in t.upper() or "人工智能" in t for t in tags)
    if not ai_tag_found:
        warnings.append("缺少 #AI 相关标签")

    # Log warnings
    if warnings:
        for w in warnings:
            logger.warning(f"[抖音质量校验] {w}")
    else:
        logger.info("[抖音质量校验] 脚本质量合格")

    return warnings


class DouyinPublisher:
    """Publishes content to Douyin via Playwright browser automation.

    Supports batch publishing: opens browser once, publishes all videos, then closes.
    """

    def __init__(self, config: "DouyinPlatformConfig"):
        self.cookie_file = config.cookie_file
        self.headless = config.headless
        self.channel = config.channel
        self.post_publish_wait = config.post_publish_wait

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

    def _wait_for_upload(self, page, timeout: int = 180) -> bool:
        """Wait for video upload to complete on Douyin Creator.

        Douyin shows a progress bar during upload. The publish button may be
        visible from the start but the upload must finish before proceeding.
        We wait for the upload progress UI to appear and then disappear.
        """
        logger.info("  Waiting for video upload to complete...")

        # Phase 1: Wait for upload progress to appear (upload has started)
        progress_seen = False
        for i in range(15):
            time.sleep(1)
            try:
                progress = page.locator('[class*="progress"]')
                if progress.count() > 0:
                    logger.info("  Upload progress detected, waiting for completion...")
                    progress_seen = True
                    break
            except Exception:
                pass

        if not progress_seen:
            logger.debug("  No progress bar found after 15s, upload may be fast or UI changed")

        # Phase 2: Wait for progress to DISAPPEAR (upload complete)
        # Minimum wait: 5s even if no progress detected
        min_wait = 5
        waited = 0
        while waited < timeout:
            time.sleep(1)
            waited += 1

            if waited % 15 == 0:
                logger.info(f"  Still waiting for upload... ({waited}s)")

            # Check if progress element has disappeared
            try:
                progress = page.locator('[class*="progress"]')
                if progress_seen and progress.count() == 0 and waited >= min_wait:
                    time.sleep(2)  # Settle
                    logger.info(f"  Upload complete after {waited}s (progress disappeared)")
                    return True
            except Exception:
                pass

            # Fallback: check for video preview/thumbnail (indicates upload done)
            if waited >= min_wait:
                try:
                    preview = page.locator('video, [class*="preview"], [class*="cover"], [class*="thumbnail"]')
                    if preview.count() > 0:
                        time.sleep(2)
                        logger.info(f"  Upload complete after {waited}s (preview detected)")
                        return True
                except Exception:
                    pass

        logger.warning(f"  Upload wait timed out after {waited}s — proceeding anyway")
        return True

    def _check_login(self, page) -> bool:
        """Check if the user is logged in to Douyin Creator.

        Uses multiple signals instead of a fragile URL check.
        Returns True if logged in, False otherwise.
        """
        # Signal 1: Known login page URLs
        login_url_patterns = ["login", "passport", "verify", "captcha"]
        current_url = page.url.lower()
        for pattern in login_url_patterns:
            if pattern in current_url:
                logger.info(f"Login page detected via URL pattern: '{pattern}'")
                return False

        # Signal 2: Login form elements (password input, SMS/phone login form)
        # Use specific, narrow selectors — avoid broad class matches
        login_selectors = [
            'input[type="password"]',
            'input[placeholder*="密码"]',
            'input[placeholder*="手机号"]',
            'button:has-text("登录")',
            '[class*="login-modal"]',
            '[class*="LoginModal"]',
        ]
        for sel in login_selectors:
            try:
                if page.locator(sel).count() > 0:
                    logger.debug(f"Login indicator found: {sel}")
                    return False
            except Exception:
                pass

        # Signal 3: Logged-in indicators (upload page content, user nav)
        logged_in_selectors = [
            'input[type="file"]',
            '[class*="upload"]',
            '[class*="header"]',
            '[class*="nav"]',
        ]
        found_indicators = 0
        for sel in logged_in_selectors:
            try:
                if page.locator(sel).count() > 0:
                    found_indicators += 1
            except Exception:
                pass

        # Need at least 2 logged-in indicators to confirm
        if found_indicators >= 2:
            return True

        # Uncertain — check if we're on the upload page at all
        if "creator" in current_url and "upload" in current_url:
            logger.info("On upload page, assuming logged in (no login indicators found)")
            return True

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

        # Re-verify login state before upload
        if not self._check_login(page):
            return {"success": False, "error": "Login expired — run: python tools/douyin_login.py"}

        # Upload video
        try:
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(str(video_path))
            logger.info(f"  Video file selected: {video_path.name}")
        except Exception as e:
            return {"success": False, "error": f"File selection failed: {e}"}

        # Wait for upload to complete
        if not self._wait_for_upload(page, timeout=180):
            logger.warning("  Upload may not have completed, proceeding anyway...")

        time.sleep(2)

        # Fill description — use short description if available, otherwise truncate
        script_text = content.get("body", content.get("script", ""))
        description = content.get("description", "")
        # Douyin only supports up to 5 tags
        tags = content.get("tags", [])[:5]
        tags_str = " ".join(tags)

        if description:
            # Use LLM-generated short description
            full_text = f"{description}\n\n{tags_str}".strip()
        else:
            # Fallback: use title + truncated script + tags
            title = content.get("title", "")
            clean_script = self._clean_script(script_text)
            # Truncate to ~100 chars max for Douyin caption
            if len(clean_script) > 100:
                clean_script = clean_script[:97] + "..."
            full_text = f"{title}\n{clean_script}\n{tags_str}".strip()

        logger.info(f"  Description: {full_text[:60]}...")

        try:
            # Try multiple selectors for the description field
            desc_selectors = [
                '[contenteditable="true"]',
                '[class*="notranslate"]',
                '.public-DraftEditor-content',
                '[data-text="true"]',
                '[class*="desc"]',
                '[placeholder*="描述"]',
                '[placeholder*="添加"]',
                '[class*="content"]',
                'textarea',
                '[role="textbox"]',
            ]
            filled = False
            for sel in desc_selectors:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible():
                        el.click()
                        time.sleep(0.5)
                        # Clear existing content
                        el.fill("")
                        # Type content with human-like delay for React state sync
                        el.type(full_text, delay=50)
                        logger.info(f"  Description filled via '{sel}' ({len(full_text)} chars)")
                        filled = True
                        break
                except Exception:
                    continue

            if not filled:
                logger.warning(f"  Could not fill description — no matching input found")
        except Exception as e:
            logger.warning(f"  Could not fill description: {e}")

        time.sleep(2)

        # Click publish
        try:
            publish_btn = page.get_by_role("button", name="发布", exact=True)
            publish_btn.wait_for(state="visible", timeout=15000)
            time.sleep(1)

            if not publish_btn.is_enabled():
                logger.warning("  Publish button is disabled — waiting...")
                page.wait_for_timeout(5000)
                if not publish_btn.is_enabled():
                    return {"success": False, "error": "Publish button remains disabled"}

            publish_btn.click()
            logger.info("  Publish button clicked!")

            # Handle potential post-publish dialogs (content declaration, copyright, etc.)
            self._handle_post_publish_dialogs(page)

            # Wait for verification/redirect
            logger.info(f"  Waiting {self.post_publish_wait}s for verification/redirect...")
            page.wait_for_timeout(self.post_publish_wait * 1000)

            final_url = page.url
            if "manage" in final_url or "success" in final_url or "content" in final_url:
                logger.info(f"  Published! -> {final_url}")
            else:
                logger.info(f"  Final URL: {final_url}")

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": f"Publish click failed: {e}"}

    def _handle_post_publish_dialogs(self, page):
        """Handle dialogs that may appear after clicking publish.

        Douyin may show:
        - Content declaration (原创声明)
        - Copyright confirmation
        - Category/tag selection
        - Captcha verification
        """
        time.sleep(3)

        # Content declaration dialog — usually has "确认" or "同意" buttons
        confirm_texts = ["确认", "同意", "知道了", "发布", "提交", "确定"]
        for text in confirm_texts:
            try:
                btn = page.get_by_role("button", name=text)
                if btn.count() > 0 and btn.is_visible():
                    logger.info(f"  Handling dialog: clicking '{text}'")
                    btn.click()
                    time.sleep(2)
            except Exception:
                pass

        # Check for checkbox agreements
        try:
            checkboxes = page.locator('input[type="checkbox"]')
            for i in range(checkboxes.count()):
                cb = checkboxes.nth(i)
                if cb.is_visible() and not cb.is_checked():
                    cb.check()
                    logger.info("  Checked agreement checkbox")
                    time.sleep(0.5)
        except Exception:
            pass

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

                # Navigate to creator center and check login status
                page.goto(UPLOAD_URL)
                page.wait_for_load_state("networkidle")
                time.sleep(3)

                # Try up to 2 times — cookies might trigger a redirect
                for attempt in range(2):
                    if self._check_login(page):
                        break
                    if attempt == 0:
                        logger.info("Login not detected on first attempt, waiting for possible redirect...")
                        page.wait_for_timeout(5000)
                        # Reload to trigger cookie-based auth
                        page.goto(UPLOAD_URL)
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)

                if not self._check_login(page):
                    current_url = page.url
                    logger.error(
                        f"Not logged in to Douyin Creator.\n"
                        f"  Current URL: {current_url}\n"
                        f"  Please run: python tools/douyin_login.py\n"
                        f"  Then try publishing again."
                    )
                    browser.close()
                    return [{"success": False, "error": "Not logged in — run: python tools/douyin_login.py"} for _ in contents]

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
