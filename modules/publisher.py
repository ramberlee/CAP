"""Publishing dispatcher module."""

import logging
from rich.console import Console
from rich.prompt import Confirm
from modules.content_store import ContentStore
from modules.config_model import AppConfig
from modules.platforms.wechat import WeChatPublisher
from modules.platforms.xiaohongshu import XiaohongshuPublisher
from modules.platforms.douyin import DouyinPublisher

logger = logging.getLogger(__name__)
console = Console()

_PUBLISHER_CLASSES = {
    "wechat": WeChatPublisher,
    "xiaohongshu": XiaohongshuPublisher,
    "douyin": DouyinPublisher,
}


class PublishDispatcher:
    def __init__(self, config: AppConfig, store: ContentStore | None = None):
        self.config = config
        self.store = store or ContentStore(
            output_dir=config.output_dir,
            media_dir=config.dashscope.media_dir,
        )
        self._publishers = {}
        for name, cls in _PUBLISHER_CLASSES.items():
            plat = getattr(config.platforms, name, None)
            if plat and plat.enabled:
                self._publishers[name] = cls(plat)

    def publish_content(self, content: dict, dry_run: bool = False) -> dict:
        """Publish a single content item."""
        platform = content["platform"]
        publisher = self._publishers.get(platform)
        if not publisher:
            return {"success": False, "error": f"No publisher for platform: {platform}"}

        if dry_run:
            logger.info(f"[DRY RUN] Would publish to {platform}: {content['title']}")
            return {"success": True, "dry_run": True, "platform": platform}

        try:
            result = publisher.publish(content)
            if result.get("success"):
                self.store.update_status(content["filepath"], "published")
            return result
        except Exception as e:
            logger.error(f"Publish failed for {content['title']}: {e}")
            return {"success": False, "error": str(e)}

    def _has_video(self, content: dict) -> bool:
        """Check if content has a video file (for Douyin)."""
        for url in content.get("media_urls", []):
            if url.endswith(".mp4"):
                return True
        return False

    def run(self, platform: str | None = None, dry_run: bool = False) -> dict:
        """List approved contents, confirm with user, then publish."""
        # Only load content for platforms that have publishers enabled
        if platform:
            contents = self.store.load_contents(platform=platform, status="approved")
        else:
            contents = []
            for p in self._publishers:
                contents.extend(self.store.load_contents(platform=p, status="approved"))

        # For Douyin, only publish content with video files
        if platform == "douyin":
            contents = [c for c in contents if self._has_video(c)]

        if not contents:
            logger.info("No approved contents to publish")
            return {"total": 0, "success": 0, "failed": 0}

        # Show what will be published
        console.print(f"\n[bold cyan]=== 待发布内容 ({len(contents)} 条) ===[/bold cyan]\n")
        for i, c in enumerate(contents, 1):
            tags_str = " ".join(c.get("tags", []))
            console.print(f"  {i}. [{c['platform']}] {c['title']}")
            if tags_str:
                console.print(f"     标签: {tags_str}")

        if dry_run:
            console.print("\n[yellow]试运行模式，不会实际发布[/yellow]")
            return {"total": len(contents), "success": len(contents), "failed": 0}

        # Ask for confirmation
        if not Confirm.ask(f"\n确认发布以上 {len(contents)} 条内容?", default=False):
            console.print("[yellow]已取消发布[/yellow]")
            return {"total": len(contents), "success": 0, "failed": 0, "cancelled": True}

        # Douyin and Xiaohongshu use batch publishing (one browser session for all posts)
        if platform in ("douyin", "xiaohongshu"):
            return self._run_batch(contents)

        # Other platforms: publish one by one
        success = 0
        failed = 0
        for content in contents:
            result = self.publish_content(content)
            if result.get("success"):
                success += 1
                console.print(f"  [green]发布成功:[/green] {content['title'][:30]}")
            else:
                failed += 1
                console.print(f"  [red]发布失败:[/red] {content['title'][:30]} - {result.get('error', '')}")

        summary = {"total": len(contents), "success": success, "failed": failed}
        logger.info(f"Publishing complete: {summary}")
        return summary

    def _run_batch(self, contents: list[dict]) -> dict:
        """Batch publish - one browser session for all posts (Douyin/Xiaohongshu)."""
        platform = contents[0]["platform"] if contents else ""
        publisher = self._publishers.get(platform)
        if not publisher:
            return {"total": 0, "success": 0, "failed": 0}

        results = publisher.publish_batch(contents)

        success = 0
        failed = 0
        for content, result in zip(contents, results):
            if result.get("success"):
                success += 1
                self.store.update_status(content["filepath"], "published")
                console.print(f"  [green]发布成功:[/green] {content['title'][:40]}")
            else:
                failed += 1
                console.print(f"  [red]发布失败:[/red] {content['title'][:40]} - {result.get('error', '')}")

        summary = {"total": len(contents), "success": success, "failed": failed}
        logger.info(f"Publishing complete: {summary}")
        return summary
