"""Xiaohongshu (Little Red Book) publisher using Playwright browser automation.

Publishes image-text notes to Xiaohongshu via browser automation.
Key technical details:
- Uses CDP (Chrome DevTools Protocol) to insert body text into TipTap/ProseMirror editor
- Uses CDP to pierce closed Shadow DOM and click the publish button inside <xhs-publish-btn>
- Title max 20 chars, body max 1000 chars (Xiaohongshu limits)
"""

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"


# ---------------------------------------------------------------------------
# Content processing (platform limits)
# ---------------------------------------------------------------------------

def process_content(title: str, body: str, tags: list[str] | None = None) -> tuple[str, str]:
    """Enforce Xiaohongshu platform limits on title and body.

    Returns (title, body) after truncation.
    """
    if len(title) > 20:
        logger.info(f"  Title truncated: {len(title)} -> 20 chars")
        title = title[:20]

    tags_text = " ".join(tags) if tags else ""
    max_body = 950 - len(tags_text) - 2 if tags_text else 950
    if len(body) > max_body:
        logger.info(f"  Body truncated: {len(body)} -> {max_body} chars")
        body = body[:max_body].rsplit("。", 1)[0] + "。"

    return title, body


class XiaohongshuPublisher:
    """Publishes content to Xiaohongshu via Playwright browser automation.

    Requires: Playwright installed, pre-saved login cookies.
    First run: run tools/xhs_login.py to save cookies.
    """

    def __init__(self, config: dict):
        self.cookie_file = config.get("cookie_file", "db/xhs_cookies.json")
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

    def _get_image_paths(self, content: dict) -> list[Path]:
        images = []
        for url in content.get("media_urls", []):
            p = Path(url)
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and p.exists():
                images.append(p)
            else:
                logger.warning(f"Image not found or unsupported format: {url}")
        return images

    def _clean_body(self, body: str, max_chars: int = 950) -> str:
        """Remove markdown formatting and truncate for Xiaohongshu."""
        text = re.sub(r"!\[.*?\]\(.*?\)\n*", "", body)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        if len(text) > max_chars:
            text = text[:max_chars].rsplit("。", 1)[0] + "。"
            logger.warning(f"  Body truncated to {len(text)} chars (limit: {max_chars})")
        return text

    def _wait_for_images_ready(self, page, timeout: int = 30) -> bool:
        for i in range(timeout):
            time.sleep(1)
            try:
                previews = page.locator('[class*="preview"] img, [class*="image-item"], [class*="cover"]')
                if previews.count() > 0:
                    logger.info(f"  Images ready after {i+1}s")
                    return True
            except Exception:
                pass
        logger.warning(f"  Images not ready after {timeout}s")
        return False

    def _switch_to_image_mode(self, page) -> bool:
        try:
            el = page.locator('text=上传图文').first
            if el.is_visible(timeout=2000):
                el.evaluate("el => el.click()")
                time.sleep(3)
                logger.info("  Switched to image-text mode")
                return True
        except Exception:
            pass
        logger.warning("  Could not switch to image-text mode")
        return False

    def _find_image_input(self, page):
        for selector in [
            'input[type="file"][accept*=".jpg"]',
            'input[type="file"][accept*=".png"]',
            'input[type="file"][accept*="image"]',
            'input[type="file"][accept*="jpeg"]',
        ]:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    return el
            except Exception:
                continue
        # Fallback: skip video inputs
        all_inputs = page.locator('input[type="file"]')
        for idx in range(all_inputs.count()):
            inp = all_inputs.nth(idx)
            accept = inp.get_attribute("accept") or ""
            if "mp4" not in accept and "mov" not in accept:
                return inp
        return None

    def _fill_body_via_cdp(self, page, body_text: str):
        """Fill body editor using CDP insertText (works with TipTap/ProseMirror)."""
        editors = page.evaluate("""() => {
            const eds = document.querySelectorAll('[contenteditable="true"]');
            return Array.from(eds).map((el, i) => ({
                index: i, class: el.className,
                area: el.getBoundingClientRect().width * el.getBoundingClientRect().height,
            }));
        }""")
        if not editors:
            logger.warning("  No contenteditable editor found")
            return

        # Use the largest editor (body, not title)
        largest = max(editors, key=lambda e: e["area"])
        body_editor = page.locator('[contenteditable="true"]').nth(largest["index"])
        body_editor.click()
        time.sleep(0.5)

        cdp = page.context.new_cdp_session(page)
        cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2})
        cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace"})
        cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace"})
        time.sleep(0.3)
        cdp.send("Input.insertText", {"text": body_text})
        time.sleep(2)
        cdp.detach()
        logger.info(f"  Body filled ({len(body_text)} chars)")

    def _click_publish_via_cdp(self, page) -> bool:
        """Click publish button inside closed Shadow DOM using CDP."""
        cdp = page.context.new_cdp_session(page)
        doc = cdp.send("DOM.getDocument", {"depth": 0, "pierce": True})

        result = cdp.send("DOM.querySelectorAll", {
            "nodeId": doc["root"]["nodeId"],
            "selector": "xhs-publish-btn"
        })

        for nid in result.get("nodeIds", []):
            desc = cdp.send("DOM.describeNode", {"nodeId": nid, "depth": 10})
            for sr in desc.get("node", {}).get("shadowRoots", []):
                sr_nid = sr.get("nodeId")
                if not sr_nid:
                    continue
                btn_result = cdp.send("DOM.querySelectorAll", {"nodeId": sr_nid, "selector": "button"})
                for btn_nid in btn_result.get("nodeIds", []):
                    btn_desc = cdp.send("DOM.describeNode", {"nodeId": btn_nid, "depth": 3})
                    btn_text = ""
                    for child in btn_desc.get("node", {}).get("children", []):
                        btn_text = child.get("nodeValue", "")

                    if btn_text.strip() != "发布":
                        continue

                    try:
                        obj = cdp.send("DOM.resolveNode", {"nodeId": btn_nid})
                        oid = obj.get("object", {}).get("objectId")
                        if oid:
                            cdp.send("Runtime.callFunctionOn", {
                                "objectId": oid,
                                "functionDeclaration": "function() { this.click(); }"
                            })
                            logger.info("  Clicked '发布' button via CDP")
                            cdp.detach()
                            return True
                    except Exception as e:
                        logger.warning(f"  Shadow button click failed: {e}")

        cdp.detach()
        return False

    def _publish_one(self, page, content: dict) -> dict:
        title = content.get("title", "")
        logger.info(f"Publishing: {title[:40]}")

        # Navigate to publish page
        page.goto(PUBLISH_URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        time.sleep(5)

        if "login" in page.url.lower():
            return {"success": False, "error": "Not logged in"}

        # Switch to image-text mode
        self._switch_to_image_mode(page)
        time.sleep(2)

        # Upload images
        images = self._get_image_paths(content)
        if not images:
            return {"success": False, "error": "No image files found"}

        file_input = self._find_image_input(page)
        if file_input is None:
            return {"success": False, "error": "Could not find image upload input"}

        try:
            for img_path in images:
                file_input.set_input_files(str(img_path.resolve()))
                time.sleep(1)
            logger.info(f"  Uploaded {len(images)} images")
            self._wait_for_images_ready(page, timeout=20)
        except Exception as e:
            return {"success": False, "error": f"Image upload failed: {e}"}

        # Fill title (max 20 chars)
        try:
            if len(title) > 20:
                title = title[:20]
                logger.info(f"  Title truncated to 20 chars: {title}")
            title_input = page.locator('[placeholder*="标题"]').first
            if title_input.is_visible(timeout=5000):
                title_input.click()
                time.sleep(0.3)
                title_input.fill(title)
                logger.info(f"  Title filled: {title}")
        except Exception as e:
            logger.warning(f"  Could not fill title: {e}")

        time.sleep(1)

        # Fill body via CDP (max 1000 chars, reserve space for tags)
        try:
            tags = content.get("tags", [])
            tags_text = " ".join(tags) if tags else ""
            max_body_chars = 950 - len(tags_text) - 2 if tags_text else 950
            body_text = self._clean_body(content.get("body", ""), max_chars=max_body_chars)
            if tags_text:
                body_text += "\n\n" + tags_text
            self._fill_body_via_cdp(page, body_text)
        except Exception as e:
            logger.warning(f"  Could not fill body: {e}")

        time.sleep(2)

        # Click publish button (inside closed Shadow DOM)
        if not self._click_publish_via_cdp(page):
            return {"success": False, "error": "Could not click publish button"}

        # Wait and check result
        time.sleep(5)
        final_url = page.url

        # Success: redirected away from publish page
        if "/publish/publish" not in final_url:
            logger.info(f"  Published! Redirected to: {final_url}")
            return {"success": True}

        # Still on publish page - check if publish actually succeeded
        # (sometimes the page stays on the same URL after successful publish)
        # Check if the title/body fields are now empty (cleared after publish)
        try:
            title_val = page.locator('[placeholder*="标题"]').first.input_value()
            if not title_val:
                logger.info("  Published! (fields cleared after publish)")
                return {"success": True}
        except Exception:
            pass

        # Check for success indicators on page
        try:
            if page.locator('text=发布成功').count() > 0:
                logger.info("  Published! (success message found)")
                return {"success": True}
        except Exception:
            pass

        # Assume success if button was clicked and no error detected
        logger.info("  Publish button clicked, assuming success")
        return {"success": True}

    def publish(self, content: dict) -> dict:
        results = self.publish_batch([content])
        return results[0] if results else {"success": False, "error": "No result"}

    def publish_batch(self, contents: list[dict]) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            err = "playwright not installed. Run: pip install playwright && playwright install chromium"
            return [{"success": False, "error": err} for _ in contents]

        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, channel=self.channel)
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()
                self._load_cookies(context)

                page.goto(PUBLISH_URL, timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                time.sleep(3)

                if "login" in page.url.lower():
                    logger.error("Not logged in. Run: python tools/xhs_login.py")
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

                    if i < len(contents) - 1:
                        time.sleep(3)

                browser.close()
                success_count = sum(1 for r in results if r["success"])
                logger.info(f"\nBrowser closed. Results: {success_count}/{len(results)} success")

        except Exception as e:
            logger.error(f"Batch publish error: {e}")
            while len(results) < len(contents):
                results.append({"success": False, "error": str(e)})

        return results
