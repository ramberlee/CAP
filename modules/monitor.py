"""Hot topic monitoring module - collects social (dao) and AI tech (shu) hotspots."""

import logging
import requests
from modules.database import Database
from modules.config_model import AppConfig

logger = logging.getLogger(__name__)


class TopicMonitor:
    def __init__(self, db: Database, config: AppConfig):
        self.db = db
        self.config = config.monitor
        self.sources_config = config.monitor.sources

    # ---- 道: Social hotspots ----

    def fetch_toutiao_hot(self) -> list[dict]:
        """Fetch trending topics from Toutiao (social hotspots -> dao)."""
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        logger.info("Fetching Toutiao hot topics...")

        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            data = resp.json()
            topics = []
            for item in data.get("data", [])[: self.config.max_topics]:
                title = item.get("Title", "").strip()
                if title:
                    topics.append({
                        "source": "toutiao",
                        "title": title,
                        "url": item.get("Url", ""),
                        "heat": item.get("HotValue", 0),
                        "category": "dao",
                    })
            logger.info(f"Fetched {len(topics)} topics from Toutiao")
            return topics
        except Exception as e:
            logger.error(f"Failed to fetch Toutiao hot topics: {e}")
            return []

    # ---- 术: AI tech hotspots ----

    def fetch_producthunt(self) -> list[dict]:
        """Fetch AI-related products from Product Hunt RSS feed (AI tech hotspots -> shu)."""
        import feedparser

        url = "https://www.producthunt.com/feed"
        logger.info("Fetching Product Hunt AI products...")

        try:
            feed = feedparser.parse(url)
            topics = []
            max_topics = self.config.max_topics

            for entry in feed.entries:
                if len(topics) >= max_topics:
                    break
                title = entry.get("title", "").strip()
                if not title:
                    continue
                summary = entry.get("summary", "")
                text = f"{title} {summary}".lower()
                topics.append({
                    "source": "producthunt",
                    "title": title,
                    "url": entry.get("link", ""),
                    "heat": 0,
                    "category": "shu",
                })

            logger.info(f"Fetched {len(topics)} AI topics from Product Hunt")
            return topics
        except Exception as e:
            logger.error(f"Failed to fetch Product Hunt topics: {e}")
            return []

    # ---- Manual & common ----

    def fetch_manual(self, titles: list[str], category: str = "dao") -> list[dict]:
        """Add manually specified topics."""
        return [
            {"source": "manual", "title": t.strip(), "url": "", "heat": 0, "category": category}
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
                category=t.get("category", "dao"),
            )
            saved += 1
            logger.info(f"Saved {t.get('category', 'dao')} topic: {t['title']}")
        return saved

    def _resolve_sources(self, category: str) -> list[str]:
        """Get enabled sources for a category from config."""
        sources = self.sources_config.get(category, [])
        if not sources:
            # Default sources if not configured
            return ["toutiao"] if category == "dao" else ["producthunt"]
        return sources

    def run(self, manual_topics: list[str] | None = None, category: str | None = None) -> int:
        """Run the full monitoring pipeline.

        Args:
            manual_topics: Optional list of manual topic titles.
            category: If set, only collect this category ('dao' or 'shu').
                      If None, collect both.

        Returns:
            Count of new topics saved.
        """
        all_topics = []

        # Collect dao (social) hotspots
        if category is None or category == "dao":
            dao_sources = self._resolve_sources("dao")
            if "toutiao" in dao_sources:
                all_topics.extend(self.fetch_toutiao_hot())

        # Collect shu (AI tech) hotspots
        if category is None or category == "shu":
            shu_sources = self._resolve_sources("shu")
            if "producthunt" in shu_sources:
                all_topics.extend(self.fetch_producthunt())

        # Add manual topics (default to dao unless specified)
        if manual_topics:
            manual_cat = category or "dao"
            all_topics.extend(self.fetch_manual(manual_topics, category=manual_cat))

        # Save to database
        new_count = self.save_topics(all_topics)
        logger.info(f"Monitoring complete: {new_count} new topics saved")
        return new_count
