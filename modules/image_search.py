"""Image search module for video scene backgrounds.

Supports multiple backends:
  - pexels:     Pexels API (free, 200 req/hour)
  - unsplash:   Unsplash API (free, 50 req/hour)
  - picsum:     Lorem Picsum placeholder images (no API key needed)
  - placeholder: Colored SVG via placeholder.com (no API key needed)

Configure via config.yaml:
  image_search:
    provider: "pexels"       # or "unsplash", "picsum", "placeholder"
    pexels_api_key: "..."
    unsplash_access_key: "..."
    download_dir: "data/images"
    orientation: "portrait"  # portrait/landscape/square
"""

from __future__ import annotations

import io
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PEXELS_BASE = "https://api.pexels.com/v1"
UNSPLASH_BASE = "https://api.unsplash.com"


@dataclass
class ImageResult:
    """A single image search result."""
    url: str           # preview/thumbnail URL
    download_url: str  # full-size download URL
    photographer: str = ""
    width: int = 0
    height: int = 0


class ImageSearcher:
    """Multi-provider image search with auto-fallback."""

    def __init__(self, config: dict):
        is_config = config.get("image_search", {})
        provider = is_config.get("provider", "placeholder")
        self.pexels_key = is_config.get("pexels_api_key", "")
        self.unsplash_key = is_config.get("unsplash_access_key", "")
        self.download_dir = Path(is_config.get("download_dir", "data/images"))
        self.orientation = is_config.get("orientation", "portrait")
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Resolve actual provider based on available keys
        if provider == "pexels" and self.pexels_key:
            self._search_fn = self._search_pexels
        elif provider == "unsplash" and self.unsplash_key:
            self._search_fn = self._search_unsplash
        elif provider in ("picsum", "placeholder"):
            self._search_fn = self._search_picsum
        else:
            logger.warning(
                f"Image search provider '{provider}' configured but no API key found. "
                f"Falling back to Picsum placeholder images."
            )
            self._search_fn = self._search_picsum

        logger.info(f"ImageSearcher: using provider={self._resolve_provider_name()}")

    def _resolve_provider_name(self) -> str:
        fn = self._search_fn
        if fn == self._search_pexels:
            return "pexels"
        if fn == self._search_unsplash:
            return "unsplash"
        if fn == self._search_picsum:
            return "picsum"
        return "unknown"

    # ── public API ──────────────────────────────────────────────

    def search(self, query: str, count: int = 3) -> list[ImageResult]:
        """Search for images matching the query. Returns top `count` results."""
        try:
            return self._search_fn(query, count)
        except Exception as e:
            logger.warning(f"Image search failed for '{query}': {e}")
            return []

    def download(self, result: ImageResult, filename: str = "", max_retries: int = 3) -> Optional[Path]:
        """Download an image result to the download directory.

        Retries on timeout/connection errors with exponential backoff.
        Returns the local Path on success, None on failure.
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                timeout = (10, 45)  # (connect_timeout, read_timeout)
                logger.info(f"Downloading: {result.download_url}" +
                           (f" (attempt {attempt+1}/{max_retries})" if attempt > 0 else ""))
                resp = requests.get(result.download_url, timeout=timeout, stream=True)
                resp.raise_for_status()

                name = filename or f"img_{uuid.uuid4().hex[:8]}"
                ct = resp.headers.get("content-type", "")
                ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
                suffix = ext_map.get(ct.split(";")[0].strip(), ".jpg")
                path = self.download_dir / f"{name}{suffix}"

                with open(path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                logger.info(f"Downloaded image: {path} ({path.stat().st_size} bytes)")
                return path

            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(f"Download timeout, retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"Image download failed after {max_retries} attempts: {e}  |  url={result.download_url}")
            except Exception as e:
                logger.error(f"Image download failed: {e}  |  url={result.download_url}")
                return None

        return None

    def search_and_download(self, query: str, filename: str = "") -> Optional[Path]:
        """Search and download the first match in one call."""
        results = self.search(query, count=1)
        if not results:
            logger.warning(f"No images found for '{query}'")
            return None
        return self.download(results[0], filename)

    # ── Pexels provider ─────────────────────────────────────────

    def _search_pexels(self, query: str, count: int) -> list[ImageResult]:
        headers = {"Authorization": self.pexels_key}
        orient = self.orientation  # portrait/landscape/square
        params = {
            "query": query,
            "per_page": min(count, 80),
            "orientation": orient,
            "size": "large",
        }
        resp = requests.get(f"{PEXELS_BASE}/search", headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for photo in data.get("photos", []):
            src = photo.get("src", {})
            results.append(ImageResult(
                url=src.get("medium", src.get("original", "")),
                download_url=src.get("original", src.get("large2x", src.get("large", ""))),
                photographer=photo.get("photographer", ""),
                width=photo.get("width", 0),
                height=photo.get("height", 0),
            ))
        logger.info(f"Pexels: found {len(results)} images for '{query}'")
        return results[:count]

    # ── Unsplash provider ───────────────────────────────────────

    def _search_unsplash(self, query: str, count: int) -> list[ImageResult]:
        headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
        orient = self.orientation
        params = {
            "query": query,
            "per_page": min(count, 30),
            "orientation": orient,
        }
        resp = requests.get(f"{UNSPLASH_BASE}/search/photos", headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for photo in data.get("results", []):
            urls = photo.get("urls", {})
            results.append(ImageResult(
                url=urls.get("small", urls.get("raw", "")),
                download_url=urls.get("regular", urls.get("raw", "")),
                photographer=photo.get("user", {}).get("name", ""),
                width=photo.get("width", 0),
                height=photo.get("height", 0),
            ))
        logger.info(f"Unsplash: found {len(results)} images for '{query}'")
        return results[:count]

    # ── Picsum placeholder provider (no API key) ────────────────

    def _search_picsum(self, query: str, count: int) -> list[ImageResult]:
        """Generate placeholder images via picsum.photos (no API key needed).

        Uses deterministic seed from query hash so same query gets same image.
        """
        seed = abs(hash(query)) % 10000
        results = []
        for i in range(count):
            seed_i = seed + i
            # 1080x1920 portrait for shorts format
            w, h = 1080, 1920
            url = f"https://picsum.photos/seed/{seed_i}/{w}/{h}"
            results.append(ImageResult(
                url=url,
                download_url=url,
                photographer="Lorem Picsum",
                width=w,
                height=h,
            ))
        logger.info(f"Picsum: using seed={seed} placeholder for '{query}'")
        return results


# ── module-level convenience ────────────────────────────────────

_searcher: Optional[ImageSearcher] = None


def get_searcher(config: dict) -> ImageSearcher:
    """Get or create the singleton ImageSearcher."""
    global _searcher
    if _searcher is None:
        _searcher = ImageSearcher(config)
    return _searcher
