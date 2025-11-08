#!/usr/bin/env python3
"""
Scrape answered Nextflow discussions for embedding.

Sources:
  1. GitHub Discussions (nextflow-io/nextflow)
  2. Seqera Community Forum

Filters:
  - Only last 2 years
  - Only answered discussions
  - Limit total count via CLI flag (default 20)

Outputs JSONL with cleaned text, ready for embeddings.

Usage:
  python scrape_nextflow_qna.py --limit 20

Requirements:
  pip install requests ratelimit tqdm beautifulsoup4
"""

import json, time, requests, argparse
from datetime import datetime, timedelta, timezone
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup

OUTPUT_DIR = Path("data/discussions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TWO_YEARS_AGO = datetime.now(timezone.utc) - timedelta(days=730)

# === RATE LIMIT CONFIG ===
@sleep_and_retry
@limits(calls=50, period=60)
def limited_get(url, **kwargs):
    return requests.get(url, **kwargs)

def html_to_text(html: str) -> str:
    """Convert HTML -> plain text for embedding"""
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(" ", strip=True)

# === GITHUB DISCUSSIONS SCRAPER ===
def fetch_github_discussions(token=None, max_pages=3, limit=20):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results = []
    base = "https://api.github.com/repos/nextflow-io/nextflow/discussions"
    params = {"state": "open", "per_page": 30}

    # Removed debugger

    for page in range(1, max_pages + 1):
        resp = limited_get(base, headers=headers, params={**params, "page": page})
        if resp.status_code != 200:
            print(f"GitHub error {resp.status_code}: {resp.text}")
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

            record = {
                "platform": "github",
                "title": d["title"],
                "url": d["html_url"],
                "text": html_to_text(d.get("body", "")),
                "answer_url": d["answer_html_url"],
                "created_at": d["created_at"],
                "author": d.get("user", {}).get("login"),
                "license": "Public under GitHub ToS",
                "source": "GitHub Discussions"
            }
            results.append(record)
            if len(results) >= limit:
                return results
        time.sleep(1)
    return results

# === SEQERA COMMUNITY SCRAPER ===
def fetch_seqera_discussions(max_pages=3, limit=20):
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

            q = html_to_text(posts[0]["cooked"])
            a = html_to_text(posts[1]["cooked"])

            results.append({
                "platform": "seqera",
                "title": t["title"],
                "url": f"{base}/t/{t['slug']}/{t['id']}",
                "text": f"Q: {q}\nA: {a}",
                "created_at": t["created_at"],
                "author": posts[0].get("username"),
                "license": "CC BY-SA 4.0",
                "source": "Seqera Community"
            })
            if len(results) >= limit:
                return results
        time.sleep(2)
    return results

# === MAIN ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20, help="Max number of records to fetch")
    args = parser.parse_args()

    gh_token = None  # optional: os.getenv("GITHUB_TOKEN")

    print(f"Fetching up to {args.limit} answered discussions (last 2 years)...")

    gh = fetch_github_discussions(token=gh_token, max_pages=10, limit=args.limit)
    seq = []
    if len(gh) < args.limit:
        seq = fetch_seqera_discussions(max_pages=10, limit=args.limit - len(gh))

    all_results = gh + seq

    # Output clean embedding-ready JSONL
    out_file = OUTPUT_DIR / "nextflow_discussions_clean.jsonl"
    with open(out_file, "w") as f:
        for item in all_results:
            f.write(json.dumps(item) + "\n")

    print(f"✅ Saved {len(all_results)} cleaned discussions → {out_file}")

