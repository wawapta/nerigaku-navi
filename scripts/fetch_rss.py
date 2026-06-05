#!/usr/bin/env python3
"""
RSS取得＋スクレイピングスクリプト for ねりがくナビ
GitHub Actions から定期実行される
"""

import feedparser
import json
import sys
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

JST = timezone(timedelta(hours=9))
OUTPUT_DIR = Path(__file__).parent.parent

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; nerigaku-navi/1.0)"
}


# ========================================
# 共通ユーティリティ
# ========================================
def now_jst():
    return datetime.now(JST).isoformat()


def parse_date_jp(text):
    """'2026年6月1日' → '2026-06-01'"""
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as res:
        charset = res.headers.get_content_charset() or "utf-8"
        return res.read().decode(charset, errors="replace")


# ========================================
# RSS取得（小P連note用）
# ========================================
def fetch_rss(source):
    label = source["label"]
    url = source["url"]
    print(f"[{label}] RSS Fetching: {url}")
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Feed parse error: {feed.bozo_exception}")

        items = []
        for e in feed.entries[:20]:
            published = None
            if hasattr(e, "published_parsed") and e.published_parsed:
                try:
                    dt = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                    published = dt.astimezone(JST).strftime("%Y-%m-%d")
                except Exception:
                    pass
            title = getattr(e, "title", "").strip()
            url_item = getattr(e, "link", "").strip()
            if title and url_item:
                items.append({"title": title, "date": published, "url": url_item})

        print(f"[{label}] OK: {len(items)}件")
        return {"updated": now_jst(), "items": items, "error": None}
    except Exception as e:
        print(f"[{label}] ERROR: {e}", file=sys.stderr)
        return {"updated": now_jst(), "items": [], "error": str(e)}


# ========================================
# スクレイピング（練馬区公式サイト用）
# ========================================
def scrape_nerima(source):
    label = source["label"]
    url = source["url"]
    base = "https://www.city.nerima.tokyo.jp"
    print(f"[{label}] Scraping: {url}")

    try:
        if not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 not installed")

        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # 練馬区の新着テーブル: <table class="list"> or <ul class="newsList">
        # パターン1: テーブル形式
        for row in soup.select("table.list tr, table tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                date_text = cols[0].get_text(strip=True)
                link_tag = cols[1].find("a")
                if link_tag:
                    date = parse_date_jp(date_text) or date_text
                    title = link_tag.get_text(strip=True)
                    href = link_tag.get("href", "")
                    if href.startswith("/"):
                        href = base + href
                    if title and href:
                        items.append({"title": title, "date": date, "url": href})

        # パターン2: リスト形式（dl/dt/dd）
        if not items:
            for dl in soup.select("dl.list, ul.newsList, .newsListArea li"):
                date_el = dl.find(class_=re.compile(r"date|day"))
                link_el = dl.find("a")
                if link_el:
                    date_text = date_el.get_text(strip=True) if date_el else ""
                    date = parse_date_jp(date_text) or date_text
                    title = link_el.get_text(strip=True)
                    href = link_el.get("href", "")
                    if href.startswith("/"):
                        href = base + href
                    if title and href:
                        items.append({"title": title, "date": date, "url": href})

        # パターン3: 汎用（日付っぽいテキスト隣のリンク）
        if not items:
            for a in soup.select("a[href]"):
                parent = a.find_parent()
                if not parent:
                    continue
                text = parent.get_text(" ", strip=True)
                date = parse_date_jp(text)
                if date:
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = base + href
                    title = a.get_text(strip=True)
                    if title and href and len(title) > 3:
                        items.append({"title": title, "date": date, "url": href})

        # 重複除去・日付降順・最大20件
        seen = set()
        unique = []
        for item in items:
            key = item["url"]
            if key not in seen:
                seen.add(key)
                unique.append(item)
        unique.sort(key=lambda x: x.get("date") or "", reverse=True)
        unique = unique[:20]

        print(f"[{label}] OK: {len(unique)}件")
        return {"updated": now_jst(), "items": unique, "error": None}

    except Exception as e:
        print(f"[{label}] ERROR: {e}", file=sys.stderr)
        return {"updated": now_jst(), "items": [], "error": str(e)}


# ========================================
# ソース定義
# ========================================
SOURCES = [
    {
        "type": "scrape",
        "label": "nerima-news",
        "url": "https://www.city.nerima.tokyo.jp/kosodatekyoiku/index.html",
        "output": "data/nerima-news.json",
    },
    {
        "type": "rss",
        "label": "nerima-events",
        "url": "https://www.city.nerima.tokyo.jp/rss/event/rss_news.xml",
        "output": "data/nerima-events.json",
    },
    {
        "type": "rss",
        "label": "kopren-note",
        "url": "https://note.com/nerima_syoup/rss",
        "output": "data/kopren-note.json",
    },
]


# ========================================
# メイン
# ========================================
def main():
    errors = []
    for source in SOURCES:
        if source["type"] == "rss":
            result = fetch_rss(source)
        else:
            result = scrape_nerima(source)

        output_path = OUTPUT_DIR / source["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if result["error"]:
            errors.append(source["label"])

    if errors:
        print(f"\n⚠ Errors: {', '.join(errors)}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✓ All sources updated successfully")


if __name__ == "__main__":
    main()
