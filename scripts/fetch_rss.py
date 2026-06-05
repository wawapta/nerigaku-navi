#!/usr/bin/env python3
"""
RSS取得スクリプト for ねりがくナビ
GitHub Actions から定期実行される
"""

import feedparser
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))

RSS_SOURCES = [
    {
        "url": "https://www.city.nerima.tokyo.jp/rss/kosodatekyoiku/rss_news.xml",
        "output": "data/nerima-news.json",
        "label": "nerima-news",
    },
    {
        "url": "https://www.city.nerima.tokyo.jp/rss/event.rss",
        "output": "data/nerima-events.json",
        "label": "nerima-events",
    },
    {
        "url": "https://note.com/atama_no_nakami/rss",
        "output": "data/kopren-note.json",
        "label": "kopren-note",
    },
]

OUTPUT_DIR = Path(__file__).parent.parent


def parse_entry(entry) -> dict:
    """feedparserエントリをJSON用dictに変換"""
    # 公開日
    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            published = dt.astimezone(JST).strftime("%Y-%m-%d")
        except Exception:
            pass

    # タイトル
    title = getattr(entry, "title", "（タイトルなし）").strip()

    # URL
    url = getattr(entry, "link", "").strip()

    return {"title": title, "date": published, "url": url}


def fetch_feed(source: dict) -> dict:
    label = source["label"]
    url = source["url"]

    print(f"[{label}] Fetching: {url}")

    try:
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            raise ValueError(f"Feed parse error: {feed.bozo_exception}")

        items = [parse_entry(e) for e in feed.entries[:20]]  # 最大20件
        items = [i for i in items if i["title"] and i["url"]]

        result = {
            "updated": datetime.now(JST).isoformat(),
            "items": items,
            "error": None,
        }
        print(f"[{label}] OK: {len(items)} items")
        return result

    except Exception as e:
        print(f"[{label}] ERROR: {e}", file=sys.stderr)
        return {
            "updated": datetime.now(JST).isoformat(),
            "items": [],
            "error": str(e),
        }


def main():
    errors = []

    for source in RSS_SOURCES:
        result = fetch_feed(source)
        output_path = OUTPUT_DIR / source["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if result["error"]:
            errors.append(source["label"])

    if errors:
        print(f"\n⚠ Errors occurred for: {', '.join(errors)}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✓ All RSS feeds updated successfully")


if __name__ == "__main__":
    main()
