"""WeChat Official Account publisher using official API."""

import logging
import re
from pathlib import Path

import requests

from modules.platforms.wechat_renderer import markdown_to_wechat_html

logger = logging.getLogger(__name__)

IMAGE_RE = re.compile(r"!\[.*?\]\((.*?)\)")


def _upload_content_image(token: str, image_path: Path) -> str | None:
    """Upload image to WeChat as permanent media for article content. Returns URL."""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(url, files={"media": (image_path.name, f, "image/png")}, timeout=30)
        data = resp.json()
        if "url" in data:
            return data["url"]
        logger.warning(f"Content image upload failed: {data}")
        return None
    except Exception as e:
        logger.error(f"Content image upload error: {e}")
        return None


def _upload_thumb(token: str, image_path: Path) -> str | None:
    """Upload image as thumb material. Returns media_id."""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb"
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(url, files={"media": (image_path.name, f, "image/png")}, timeout=30)
        data = resp.json()
        if "media_id" in data:
            return data["media_id"]
        logger.warning(f"Thumb upload failed: {data}")
        return None
    except Exception as e:
        logger.error(f"Thumb upload error: {e}")
        return None


class WeChatPublisher:
    BASE_URL = "https://api.weixin.qq.com/cgi-bin"

    def __init__(self, config: dict):
        self.app_id = config.get("app_id", "")
        self.app_secret = config.get("app_secret", "")
        self.author = config.get("author", "")
        self.mode = config.get("mode", "draft")
        self.theme = config.get("theme", "claude")
        self._access_token = None

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        url = f"{self.BASE_URL}/token"
        params = {"grant_type": "client_credential", "appid": self.app_id, "secret": self.app_secret}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Failed to get access token: {data}")
        self._access_token = data["access_token"]
        return self._access_token

    def publish(self, content: dict) -> dict:
        if not self.app_id or not self.app_secret:
            return {"success": False, "error": "WeChat app_id/app_secret not configured"}

        try:
            token = self._get_access_token()
            body = content["body"]
            base_dir = Path(content.get("filepath", "")).parent if content.get("filepath") else Path(".")

            # Upload content images and first image as thumb
            image_urls = {}
            thumb_media_id = None
            for match in IMAGE_RE.finditer(body):
                local_ref = match.group(1)
                img_path = (base_dir / local_ref).resolve()
                if not img_path.exists():
                    continue

                # Upload as content image
                wechat_url = _upload_content_image(token, img_path)
                if wechat_url:
                    image_urls[local_ref] = wechat_url

                # Use first image as thumb
                if thumb_media_id is None:
                    thumb_media_id = _upload_thumb(token, img_path)

            # Replace local image paths with WeChat URLs
            for local_ref, wechat_url in image_urls.items():
                body = body.replace(f"]({local_ref})", f"]({wechat_url})")

            # Convert markdown to WeChat HTML using the renderer
            html_content = markdown_to_wechat_html(body, self.theme)

            # Create draft (WeChat limits: title 32 chars, author 16 chars, digest 128 chars)
            title = content["title"]
            if len(title) > 32:
                title = title[:32]
            author = self.author
            if len(author) > 16:
                author = author[:16]
            digest = content.get("summary", "")
            if not digest:
                # Auto-generate digest from first paragraph
                for line in body.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("!") and not line.startswith("-"):
                        digest = re.sub(r"\*\*(.*?)\*\*", r"\1", line)  # strip bold markers
                        break
            # WeChat limits digest to 128 bytes (not chars); CJK chars = 3 bytes each
            while len(digest.encode("utf-8")) > 120:
                digest = digest[:-1]
            if digest:
                digest = digest.rstrip() + "…"

            url = f"{self.BASE_URL}/draft/add?access_token={token}"
            article = {
                "title": title,
                "author": author,
                "digest": digest,
                "content": html_content,
                "content_source_url": "",
                "need_open_comment": 0,
            }
            if thumb_media_id:
                article["thumb_media_id"] = thumb_media_id
            else:
                return {"success": False, "error": "No images found — WeChat draft requires a cover image. Add at least one [IMAGE:] placeholder."}

            import json
            payload = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
            resp = requests.post(url, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30)
            result = resp.json()

            if "media_id" in result:
                logger.info(f"WeChat draft created: {result['media_id']}")
                return {
                    "success": True,
                    "mode": "draft",
                    "media_id": result["media_id"],
                    "message": "Draft created. Go to WeChat admin panel to publish.",
                }
            else:
                return {"success": False, "error": str(result)}

        except Exception as e:
            return {"success": False, "error": str(e)}
