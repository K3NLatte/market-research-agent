import json
import os
from datetime import datetime, timezone

import feedparser

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


FEEDS = [
    # Security
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.darkreading.com/rss_simple.asp",
    # IT / Web
    "https://hnrss.org/frontpage",
    "https://techcrunch.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/index",
    # Finance
    "https://www.ft.com/world?format=rss",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]


def summarize_text(client, text):
    if client is None:
        return text[:300]

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"次のニュースを日本語で3行に要約してください:\n{text}",
    )
    return response.output_text.strip()


def build_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def collect_articles():
    collected = []
    seen_links = set()

    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            link = entry.get("link", "").strip()
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            collected.append(
                {
                    "title": entry.get("title", "").strip(),
                    "link": link,
                    "raw_summary": entry.get("summary", "").strip(),
                    "source": feed.feed.get("title", url),
                    "published": entry.get("published", ""),
                }
            )
    return collected


def main():
    client = build_client()
    articles = collect_articles()

    for item in articles:
        base_text = f"{item['title']}\n{item['raw_summary']}"
        item["summary"] = summarize_text(client, base_text)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "articles": articles,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(articles)} articles to data/news.json")


if __name__ == "__main__":
    main()
