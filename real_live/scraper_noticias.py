"""
scraper_noticias.py — Neutro-Safe Live Data
Scrapes RSS feeds from Guayaquil media and returns relevant articles
about urban violence, security, and structural drivers.
No API key required.
"""
from __future__ import annotations
import feedparser
import requests
import re
from datetime import datetime, timezone
from pathlib import Path
import json
import time

# ── RSS feeds de medios ecuatorianos ─────────────────────────────────────────
RSS_FEEDS = {
    "El Universo":  "https://www.eluniverso.com/arc/outboundfeeds/rss/",
    "El Comercio":  "https://www.elcomercio.com/feed/",
    "La Hora":      "https://lahora.com.ec/feed/",
    "El Telégrafo": "https://www.eltelegrafo.com.ec/feed/",
    "Primicias":    "https://www.primicias.ec/feed/",
    "GK City":      "https://gk.city/feed/",
}

# Palabras clave para filtrar artículos relevantes
KEYWORDS_ES = [
    "violencia", "homicidio", "femicidio", "asesinato", "crimen",
    "seguridad", "inseguridad", "pandilla", "banda", "narco",
    "extorsión", "extorsion", "secuestro", "robo", "asalto",
    "Guayaquil", "Bastión", "Guasmo", "Trinitaria", "Suburbio",
    "policía", "policia", "fiscal", "delito", "corrupción",
    "corrupcion", "impunidad", "cárcel", "carcel", "prisión",
    "prisiones", "armas", "drogas", "tráfico", "trafico",
]

ARTICLES_CACHE = Path(__file__).parent.parent / "real_data" / "noticias_cache.json"


def is_relevant(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in KEYWORDS_ES)


def scrape_feeds(max_per_feed: int = 8, verbose: bool = True) -> list[dict]:
    articles = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                title   = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link    = entry.get("link", "")
                pub     = entry.get("published", "")
                if is_relevant(title, summary):
                    articles.append({
                        "source":  source,
                        "title":   title,
                        "summary": summary[:800],
                        "url":     link,
                        "published": pub,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                        "lang": "es",
                    })
                    count += 1
                    if count >= max_per_feed:
                        break
            if verbose:
                print(f"  {source}: {count} artículos relevantes")
        except Exception as e:
            if verbose:
                print(f"  {source}: error — {e}")
        time.sleep(0.5)
    return articles


def load_cached() -> list[dict]:
    if ARTICLES_CACHE.exists():
        return json.loads(ARTICLES_CACHE.read_text(encoding="utf-8"))
    return []


def save_cache(articles: list[dict], keep_days: int = 30) -> None:
    existing = load_cached()
    # Merge: keep existing + add new (dedup by url)
    urls_existing = {a["url"] for a in existing}
    new = [a for a in articles if a["url"] not in urls_existing]
    merged = existing + new
    # Keep only last N days
    cutoff = datetime.now(timezone.utc).timestamp() - keep_days * 86400
    merged = [a for a in merged
              if _parse_ts(a.get("scraped_at", "")).timestamp() > cutoff]
    ARTICLES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    ARTICLES_CACHE.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Cache: {len(merged)} artículos ({len(new)} nuevos)")
    return merged


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.now(timezone.utc)


def run(verbose: bool = True) -> list[dict]:
    if verbose:
        print("=== Scraping RSS feeds ===")
    fresh = scrape_feeds(verbose=verbose)
    save_cache(fresh)
    all_articles = load_cached()
    if verbose:
        print(f"Total en cache: {len(all_articles)} artículos")
    return all_articles


if __name__ == "__main__":
    arts = run()
    print("\nMuestra (primeros 3):")
    for a in arts[:3]:
        print(f"  [{a['source']}] {a['title'][:80]}")
