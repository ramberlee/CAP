"""Hot topic monitoring module - collects social (dao) and AI tech (shu) hotspots."""

import logging
import requests
from modules.database import Database

logger = logging.getLogger(__name__)

# AI-related keywords for filtering Hacker News topics
AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "chatgpt", "openai",
    "machine learning", "deep learning", "neural", "transformer", "diffusion",
    "stable diffusion", "midjourney", "copilot", "gemini", "claude", "anthropic",
    "langchain", "rag", "fine-tune", "fine tuning", "embedding", "vector",
    "generative", "agi", "multimodal", "prompt", "agent", "mcp",
]


class TopicMonitor:
    def __init__(self, db: Database, config: dict):
        self.db = db
        self.config = config.get("monitor", {})
        self.sources_config = self.config.get("sources", {})

    # ---- 道: Social hotspots ----

    def fetch_toutiao_hot(self) -> list[dict]:
        """Fetch trending topics from Toutiao (social hotspots -> dao)."""
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
                        "category": "dao",
                    })
            logger.info(f"Fetched {len(topics)} topics from Toutiao")
            return topics
        except Exception as e:
            logger.error(f"Failed to fetch Toutiao hot topics: {e}")
            return []

    # ---- 术: AI tech hotspots ----

    def fetch_36kr(self) -> list[dict]:
        """Fetch AI/tech newsflash from 36kr (AI tech hotspots -> shu)."""
        url = "https://36kr.com/api/newsflash"
        logger.info("Fetching 36kr AI/tech news...")

        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                params={"per_page": 50},
                timeout=10,
            )
            data = resp.json()
            topics = []
            for item in data.get("data", {}).get("items", []):
                title = item.get("title", "").strip()
                if not title:
                    continue
                # Filter for AI/tech related content
                desc = item.get("description", "")
                summary = item.get("summary", "")
                text = f"{title} {desc} {summary}".lower()
                if not any(kw in text for kw in AI_KEYWORDS):
                    continue
                topics.append({
                    "source": "36kr",
                    "title": title,
                    "url": f"https://36kr.com/p/{item.get('id', '')}",
                    "heat": 0,
                    "category": "shu",
                })
                if len(topics) >= self.config.get("max_topics", 10):
                    break
            logger.info(f"Fetched {len(topics)} AI topics from 36kr")
            return topics
        except Exception as e:
            logger.error(f"Failed to fetch 36kr topics: {e}")
            return []

    def fetch_hacker_news(self) -> list[dict]:
        """Fetch AI-related top stories from Hacker News (AI tech hotspots -> shu)."""
        logger.info("Fetching Hacker News AI topics...")

        try:
            # Get top story IDs
            resp = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=10,
            )
            story_ids = resp.json()[:100]  # Check top 100 stories

            topics = []
            for sid in story_ids:
                if len(topics) >= self.config.get("max_topics", 10):
                    break
                try:
                    item_resp = requests.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                        timeout=5,
                    )
                    item = item_resp.json()
                    if not item or item.get("type") != "story":
                        continue

                    title = item.get("title", "")
                    text = title.lower()
                    if not any(kw in text for kw in AI_KEYWORDS):
                        continue

                    topics.append({
                        "source": "hackernews",
                        "title": title,
                        "url": item.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        "heat": item.get("score", 0),
                        "category": "shu",
                    })
                except Exception:
                    continue

            logger.info(f"Fetched {len(topics)} AI topics from Hacker News")
            return topics
        except Exception as e:
            logger.error(f"Failed to fetch Hacker News topics: {e}")
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
            return ["toutiao"] if category == "dao" else ["36kr", "hackernews"]
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
            if "36kr" in shu_sources:
                all_topics.extend(self.fetch_36kr())
            if "hackernews" in shu_sources:
                all_topics.extend(self.fetch_hacker_news())

        # Add manual topics (default to dao unless specified)
        if manual_topics:
            manual_cat = category or "dao"
            all_topics.extend(self.fetch_manual(manual_topics, category=manual_cat))

        # Save to database
        new_count = self.save_topics(all_topics)
        logger.info(f"Monitoring complete: {new_count} new topics saved")
        return new_count
