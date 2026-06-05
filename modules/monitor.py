"""Hot topic monitoring module."""

import logging
import requests
from modules.database import Database

logger = logging.getLogger(__name__)


class TopicMonitor:
    def __init__(self, db: Database, config: dict):
        self.db = db
        self.config = config.get("monitor", {})

    def fetch_toutiao_hot(self) -> list[dict]:
        """Fetch trending topics from Toutiao."""
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        logger.info("Fetching Toutiao hot topics...")

        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            data = resp.json()
            topics = []
            for item in data.get("data", [])[: self.config.get("max_topics", 10)]:
                title = item.get("Title", "").strip()
                if title:
                    topics.append({
                        "source": "toutiao",
                        "title": title,
                        "url": item.get("Url", ""),
                        "heat": item.get("HotValue", 0),
                    })
            logger.info(f"Fetched {len(topics)} topics from Toutiao")
            return topics
        except Exception as e:
            logger.error(f"Failed to fetch Toutiao hot topics: {e}")
            return []

    def fetch_manual(self, titles: list[str]) -> list[dict]:
        """Add manually specified topics."""
        return [
            {"source": "manual", "title": t.strip(), "url": "", "heat": 0}
            for t in titles
            if t.strip()
        ]

    def save_topics(self, topics: list[dict]) -> int:
        """Save topics to database, skip duplicates. Returns count of new topics."""
        saved = 0
        for t in topics:
            if not t["title"]:
                continue
            if self.db.topic_exists(t["title"]):
                logger.debug(f"Skipping duplicate topic: {t['title']}")
                continue
            self.db.add_topic(
                source=t["source"],
                title=t["title"],
                url=t.get("url", ""),
                heat=t.get("heat", 0),
            )
            saved += 1
            logger.info(f"Saved topic: {t['title']}")
        return saved

    def run(self, manual_topics: list[str] | None = None) -> int:
        """Run the full monitoring pipeline. Returns count of new topics saved."""
        all_topics = []

        # Fetch from Toutiao
        all_topics.extend(self.fetch_toutiao_hot())

        # Add manual topics
        if manual_topics:
            all_topics.extend(self.fetch_manual(manual_topics))

        # Save to database
        new_count = self.save_topics(all_topics)
        logger.info(f"Monitoring complete: {new_count} new topics saved")
        return new_count
