"""File-based content storage using Markdown + YAML frontmatter."""

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

PLATFORM_DIR_NAMES = {
    "xiaohongshu": "小红书",
    "wechat": "微信公众号",
    "douyin": "抖音",
}


class ContentStore:
    def __init__(self, output_dir: str = "output", media_dir: str = "media"):
        self.output_dir = Path(output_dir)
        self.media_dir = Path(media_dir)

    def _platform_dir(self, platform: str) -> Path:
        d = self.output_dir / platform
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _next_seq(self, platform_dir: Path) -> int:
        existing = list(platform_dir.glob("*.md"))
        if not existing:
            return 1
        nums = []
        for f in existing:
            m = re.match(r"(\d+)_", f.name)
            if m:
                nums.append(int(m.group(1)))
        return max(nums, default=0) + 1

    def _safe_filename(self, title: str) -> str:
        safe = re.sub(r'[\\/:*?"<>|\s]+', "_", title)[:30]
        return safe.strip("_") or "untitled"

    def save_content(
        self,
        platform: str,
        title: str,
        body: str,
        tags: list[str] | None = None,
        media_urls: list[str] | None = None,
        topic_id: int | None = None,
    ) -> Path:
        """Save content as a markdown file. Returns the file path."""
        platform_dir = self._platform_dir(platform)
        seq = self._next_seq(platform_dir)
        safe_title = self._safe_filename(title)
        filename = f"{seq:03d}_{safe_title}.md"
        filepath = platform_dir / filename

        frontmatter = {
            "platform": platform,
            "status": "approved",
            "tags": tags or [],
            "media_urls": [f"media/{Path(u).name}" for u in (media_urls or [])],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        if topic_id is not None:
            frontmatter["topic_id"] = topic_id

        content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=True).strip()}\n---\n\n"
        content += f"# {title}\n\n{body}\n"

        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Content saved: {filepath}")
        return filepath

    def load_content(self, filepath: Path) -> Optional[dict]:
        """Load a single content file. Returns dict with metadata + body."""
        try:
            text = filepath.read_text(encoding="utf-8")
            meta = {}
            body = text

            m = FRONTMATTER_RE.match(text)
            if m:
                meta = yaml.safe_load(m.group(1)) or {}
                body = text[m.end():]

            # Extract title from first # heading
            title = ""
            for line in body.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            # Strip the title line from body for display
            if title:
                body = body.lstrip()
                if body.startswith(f"# {title}"):
                    body = body[len(f"# {title}"):].lstrip("\n")

            return {
                "filepath": str(filepath),
                "filename": filepath.name,
                "platform": meta.get("platform", filepath.parent.name),
                "status": meta.get("status", "approved"),
                "title": title,
                "body": body,
                "tags": meta.get("tags", []),
                "media_urls": meta.get("media_urls", []),
                "created_at": meta.get("created_at", ""),
                "topic_id": meta.get("topic_id"),
            }
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return None

    def load_contents(
        self,
        platform: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """Load all content files, optionally filtered."""
        results = []
        platforms = [platform] if platform else ["xiaohongshu", "wechat", "douyin"]

        for p in platforms:
            pdir = self._platform_dir(p)
            for f in sorted(pdir.glob("*.md")):
                item = self.load_content(f)
                if item and (status is None or item["status"] == status):
                    results.append(item)

        return results

    def update_status(self, filepath: str | Path, new_status: str):
        """Update status in a content file's frontmatter."""
        filepath = Path(filepath)
        text = filepath.read_text(encoding="utf-8")

        m = FRONTMATTER_RE.match(text)
        if m:
            meta = yaml.safe_load(m.group(1)) or {}
            meta["status"] = new_status
            new_frontmatter = f"---\n{yaml.dump(meta, allow_unicode=True, default_flow_style=True).strip()}\n---\n"
            new_text = new_frontmatter + text[m.end():]
        else:
            # No frontmatter, prepend one
            meta = {"status": new_status}
            new_frontmatter = f"---\n{yaml.dump(meta, allow_unicode=True, default_flow_style=True).strip()}\n---\n\n"
            new_text = new_frontmatter + text

        filepath.write_text(new_text, encoding="utf-8")
        logger.info(f"Status updated to '{new_status}': {filepath}")

    def get_stats(self) -> dict:
        """Count contents by platform and status."""
        stats = {"total": 0, "approved": 0, "published": 0}
        for p in ["xiaohongshu", "wechat", "douyin"]:
            pdir = self._platform_dir(p)
            for f in pdir.glob("*.md"):
                stats["total"] += 1
                item = self.load_content(f)
                if item:
                    s = item.get("status", "approved")
                    stats[s] = stats.get(s, 0) + 1
        return stats
