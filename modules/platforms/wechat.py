"""WeChat Official Account publisher using official API."""

import json
import logging
import re
from pathlib import Path

import requests
from openai import OpenAI

from modules.platforms.wechat_renderer import markdown_to_wechat_html

logger = logging.getLogger(__name__)

IMAGE_RE = re.compile(r"!\[.*?\]\((.*?)\)")


# ---------------------------------------------------------------------------
# Content validation & repair (LLM-based)
# ---------------------------------------------------------------------------

CATEGORY_SYSTEM_PROMPTS = {
    "dao": (
        "你是MiMo，是小米公司研发的AI智能助手。"
        "你正在为一个AI领域的内容账号创作「道」系列内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
        "「道」系列关注社会趋势、人性洞察、时代变迁，用AI思维提供独特的观察视角。"
        "内容要求：从宏观视角解读社会热点，提供认知升级的洞察，而非就事论事。"
        "请严格按照要求的JSON格式输出。"
    ),
    "shu": (
        "你是MiMo，是小米公司研发的AI智能助手。"
        "你正在为一个AI领域的内容账号创作「术」系列内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
        "「术」系列关注AI技术本身，解读技术原理、应用场景、实操方法。"
        "内容要求：有具体的技术细节、工具名称、使用方法，提供实操价值，而非泛泛而谈。"
        "请严格按照要求的JSON格式输出。"
    ),
}


def validate_content(result: dict, category: str = "dao", client: OpenAI = None, model: str = "mimo-v2.5-pro") -> list[str]:
    """Validate WeChat content against template requirements using LLM.

    Returns a list of issues found. Empty list means content passes validation.
    """
    if not client:
        logger.warning("[微信质量校验] 未提供 LLM client，跳过校验")
        return []

    title = result.get("title", "")
    summary = result.get("summary", "")
    body = result.get("body", "")

    validation_prompt = f"""你是一个严格的内容审核专家。请检查以下微信公众号文章是否符合要求，返回 JSON 格式的检查结果。

## 检查要求
1. **标题**：不超过 32 字，简洁有力，能引发点击欲望
2. **摘要**：不超过 50 字，一句话概括文章核心
3. **正文**：1500-2500 字（中文字符），结构清晰，有小标题分段
4. **结构**：
   - 开头：用热点故事/数据/问题引入
   - 中间：2-3 个核心论点，每个论点配案例或数据
   - 结尾：提炼洞察 + 引导互动
5. **格式**：使用 Markdown 格式，有小标题
6. **配图**：正文中有 2-4 个 [IMAGE:图片描述] 占位符
7. **AI 关联**：必须从 AI 时代视角提供独特洞察

## 待检查的文章
标题：{title}
摘要：{summary}
正文：
{body[:3000]}

## 输出格式（严格 JSON）
```json
{{
  "pass": true/false,
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}}
```

如果完全符合要求，pass 为 true，issues 为空数组。如果有任何不符合，pass 为 false，列出具体问题。"""

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=512,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "你是内容质量审核专家，严格按 JSON 格式输出。"},
                {"role": "user", "content": validation_prompt},
            ],
        )
        text = response.choices[0].message.content

        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            logger.warning("[微信质量校验] LLM 返回无 JSON，跳过校验")
            return []

        check = json.loads(text[json_start:json_end])
        issues = check.get("issues", [])

        if check.get("pass", False):
            logger.info("[微信质量校验] 内容质量合格")
            return []

        for issue in issues:
            logger.warning(f"[微信质量校验] {issue}")
        if check.get("suggestions"):
            for s in check["suggestions"]:
                logger.info(f"[微信质量校验] 建议: {s}")

        return issues

    except Exception as e:
        logger.warning(f"[微信质量校验] 校验失败: {e}")
        return []


def repair_content(result: dict, issues: list[str], category: str = "dao", client: OpenAI = None, model: str = "mimo-v2.5-pro", max_tokens: int = 4096) -> dict | None:
    """Repair WeChat content based on validation issues using LLM.

    Returns repaired result dict, or None if repair fails.
    """
    if not client:
        logger.warning("[微信修复] 未提供 LLM client，跳过修复")
        return None

    title = result.get("title", "")
    summary = result.get("summary", "")
    body = result.get("body", "")

    issues_text = "\n".join(f"- {i}" for i in issues)

    repair_prompt = f"""你是一个专业的微信公众号内容创作者。以下文章存在质量问题，请修复后返回完整的修正版本。

## 需要修复的问题
{issues_text}

## 原文
标题：{title}
摘要：{summary}
正文：
{body}

## 修复要求
1. 保持原文的核心观点和风格
2. 修复上述列出的所有问题
3. 标题不超过 32 字
4. 摘要不超过 50 字
5. 正文 1500-2500 字，Markdown 格式，有小标题
6. 正文中包含 2-4 个 [IMAGE:图片描述] 占位符
7. 从 AI 时代视角提供洞察

## 输出格式（严格 JSON）
```json
{{
  "title": "修正后的标题",
  "summary": "修正后的摘要",
  "body": "修正后的正文（Markdown格式）"
}}
```"""

    try:
        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(category, CATEGORY_SYSTEM_PROMPTS["dao"])
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": repair_prompt},
            ],
        )
        text = response.choices[0].message.content

        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            logger.error("[微信修复] LLM 返回无 JSON，修复失败")
            return None

        repaired = json.loads(text[json_start:json_end])
        logger.info(f"[微信修复] 修复完成: {repaired.get('title', 'N/A')[:30]}")
        return repaired

    except Exception as e:
        logger.error(f"[微信修复] 修复失败: {e}")
        return None


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

    def __init__(self, config: "WeChatPlatformConfig"):
        self.app_id = config.app_id
        self.app_secret = config.app_secret
        self.author = config.author
        self.mode = config.mode
        self.theme = config.theme
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
