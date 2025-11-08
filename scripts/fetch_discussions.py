#!/usr/bin/env python3
"""
Fetch Nextflow discussions from GitHub and Seqera Community.

Part 1: Scraping - Fetches raw discussion data from APIs.
Outputs raw JSON file with all data.

Usage:
  python fetch_discussions.py --limit 100 --output data/discussions/raw_discussions.json

Requirements:
  pip install requests ratelimit beautifulsoup4
"""

import json
import time
import requests
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from ratelimit import limits, sleep_and_retry
from bs4 import BeautifulSoup

OUTPUT_DIR = Path("scripts/data/discussions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TWO_YEARS_AGO = datetime.now(timezone.utc) - timedelta(days=730)

# === RATE LIMIT CONFIG ===
@sleep_and_retry
@limits(calls=50, period=60)
def limited_get(url, **kwargs):
    return requests.get(url, **kwargs)


def html_to_text(html: str) -> str:
    """Convert HTML -> plain text."""
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(" ", strip=True)


# === GITHUB DISCUSSIONS SCRAPER ===
def fetch_github_discussions(token=None, max_pages=10, limit=100):
    """Fetch discussions from GitHub API."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results = []
    base = "https://api.github.com/repos/nextflow-io/nextflow/discussions"
    params = {"state": "open", "per_page": 30}

    for page in range(1, max_pages + 1):
        resp = limited_get(base, headers=headers, params={**params, "page": page})
        if resp.status_code != 200:
            print(f"GitHub error {resp.status_code}: {resp.text[:200]}")
            break

        data = resp.json()
        if not data:
            break

        for d in data:
            created = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00"))
            if created < TWO_YEARS_AGO:
                continue
            if not d.get("answer_html_url"):
                continue

            # Keep all raw data for cleaning step
            record = {
                "platform": "github",
                "title": d["title"],
                "url": d["html_url"],
                "body_html": d.get("body", ""),
                "body_text": html_to_text(d.get("body", "")),
                "answer_url": d["answer_html_url"],
                "created_at": d["created_at"],
                "updated_at": d.get("updated_at"),
                "author": d.get("user", {}).get("login"),
                "author_info": d.get("user", {}),  # Full user object (will clean later)
                "labels": d.get("labels", []),
                "comments": d.get("comments", 0),
                "category": d.get("category", {}),
                "raw_data": d  # Keep full raw data for reference
            }
            results.append(record)
            if len(results) >= limit:
                return results
        time.sleep(1)
    return results


# === SEQERA COMMUNITY SCRAPER ===
def fetch_seqera_discussions(max_pages=10, limit=100):
    """Fetch discussions from Seqera Community Forum."""
    base = "https://community.seqera.io"
    results = []

    for page in range(0, max_pages):
        url = f"{base}/c/nextflow/5.json?page={page}"
        resp = limited_get(url)
        if resp.status_code != 200:
            break

        topics = resp.json().get("topic_list", {}).get("topics", [])
        for t in topics:
            created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            if created < TWO_YEARS_AGO:
                continue

            topic_url = f"{base}/t/{t['id']}.json"
            topic_resp = limited_get(topic_url)
            if topic_resp.status_code != 200:
                continue

            thread = topic_resp.json()
            posts = thread.get("post_stream", {}).get("posts", [])
            if len(posts) < 2:
                continue

            q_html = posts[0].get("cooked", "")
            a_html = posts[1].get("cooked", "")
            q_text = html_to_text(q_html)
            a_text = html_to_text(a_html)

            results.append({
                "platform": "seqera",
                "title": t["title"],
                "url": f"{base}/t/{t['slug']}/{t['id']}",
                "question_html": q_html,
                "question_text": q_text,
                "answer_html": a_html,
                "answer_text": a_text,
                "body_text": f"Q: {q_text}\nA: {a_text}",
                "created_at": t["created_at"],
                "updated_at": t.get("updated_at"),
                "author": posts[0].get("username"),
                "author_info": posts[0].get("user", {}),  # Full user object (will clean later)
                "answer_author": posts[1].get("username"),
                "answer_author_info": posts[1].get("user", {}),  # Full user object (will clean later)
                "raw_data": thread  # Keep full raw data for reference
            })
            if len(results) >= limit:
                return results
        time.sleep(2)
    return results


# === MAIN ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Nextflow discussions from GitHub and Seqera")
    parser.add_argument("--limit", type=int, default=100, help="Max number of records to fetch")
    parser.add_argument("--output", type=str, default="scripts/data/discussions/raw_discussions.json",
                       help="Output file path")
    parser.add_argument("--github-token", type=str, default=None,
                       help="GitHub API token (optional, increases rate limit)")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching up to {args.limit} answered discussions (last 2 years)...")

    gh = fetch_github_discussions(token=args.github_token, max_pages=10, limit=args.limit)
    print(f"✓ Fetched {len(gh)} discussions from GitHub")

    seq = []
    if len(gh) < args.limit:
        seq = fetch_seqera_discussions(max_pages=10, limit=args.limit - len(gh))
        print(f"✓ Fetched {len(seq)} discussions from Seqera")

    all_results = gh + seq

    # Save raw JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(all_results)} raw discussions → {output_path}")
    print(f"   Next step: Run clean_discussions.py to clean and format for vector store")

