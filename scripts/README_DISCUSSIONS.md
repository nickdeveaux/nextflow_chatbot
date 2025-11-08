# Nextflow Discussions Scraping & Cleaning

This directory contains scripts to fetch and clean Nextflow discussions from GitHub and Seqera Community for vector store indexing.

## Overview

The process is split into two steps:

1. **Fetch** (`fetch_discussions.py`) - Scrapes raw discussion data from APIs
2. **Clean** (`clean_discussions.py`) - Removes avatar URLs, user data, and formats for vector store

## Setup

Install required dependencies:

```bash
pip install requests ratelimit beautifulsoup4
```

## Usage

### Step 1: Fetch Discussions

Fetch raw discussions from GitHub and Seqera:

```bash
python scripts/fetch_discussions.py \
  --limit 100 \
  --output scripts/data/discussions/raw_discussions.json \
  --github-token YOUR_GITHUB_TOKEN  # Optional, increases rate limit
```

**Options:**
- `--limit`: Maximum number of discussions to fetch (default: 100)
- `--output`: Output file path (default: `scripts/data/discussions/raw_discussions.json`)
- `--github-token`: GitHub API token (optional, increases rate limit from 60 to 5000 requests/hour)

**What it does:**
- Fetches answered discussions from GitHub Discussions (nextflow-io/nextflow)
- Fetches discussions from Seqera Community Forum
- Filters to last 2 years only
- Saves raw JSON with all data (including user info, avatars, etc.)

### Step 2: Clean Discussions

Clean and format discussions for vector store:

```bash
python scripts/clean_discussions.py \
  --input scripts/data/discussions/raw_discussions.json \
  --output scripts/data/discussions/clean_discussions.json \
  --format vector_store
```

**Options:**
- `--input`: Input raw discussions JSON file (required)
- `--output`: Output cleaned discussions JSON file (required)
- `--format`: Output format - `vector_store` (for indexing) or `simple` (cleaned only, default: `vector_store`)

**What it does:**
- Removes avatar URLs (GitHub avatars, gravatars, etc.)
- Removes user profile data (author_info, user objects)
- Removes unnecessary metadata (raw_data, debug info)
- Formats text for embeddings
- Creates metadata structure for vector store
- Filters out empty/invalid discussions

## Output Format

### Raw Format (from fetch_discussions.py)

Raw JSON with all data:

```json
{
  "platform": "github",
  "title": "Discussion Title",
  "url": "https://github.com/...",
  "body_html": "<html>...</html>",
  "body_text": "Plain text content",
  "author": "username",
  "author_info": {
    "avatar_url": "https://avatars.githubusercontent.com/...",
    "login": "username",
    ...
  },
  "raw_data": { ... }
}
```

### Clean Format (from clean_discussions.py)

Cleaned JSON ready for vector store:

```json
{
  "text": "Cleaned text content without avatar URLs",
  "metadata": {
    "platform": "github",
    "source": "GitHub Discussions",
    "url": "https://github.com/...",
    "title": "Discussion Title",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## Integration with Vector Store

The cleaned discussions can be integrated into the vector store by:

1. **Manual Integration**: Load the cleaned JSON and add to vector store index
2. **Automatic Integration**: Modify `document_loader.py` to load discussions alongside docs

Example integration in `document_loader.py`:

```python
def load_discussions(json_path: Path) -> List[Dict]:
    """Load cleaned discussions from JSON."""
    with open(json_path, 'r') as f:
        discussions = json.load(f)
    return discussions

# In prepare_documents_for_indexing:
discussions = load_discussions(Path("scripts/data/discussions/clean_discussions.json"))
for disc in discussions:
    documents.append({
        'text': disc['text'],
        'metadata': disc['metadata']
    })
```

## Rate Limits

- **GitHub API**: 60 requests/hour (unauthenticated) or 5000 requests/hour (with token)
- **Seqera Community**: No official limit, but we use 2-second delays between requests

## Notes

- Only fetches discussions from the last 2 years
- Only includes answered discussions (GitHub) or discussions with at least 2 posts (Seqera)
- Avatar URLs are removed using regex patterns
- User data is completely removed for privacy
- Text is cleaned but structure is preserved

## Troubleshooting

### GitHub API Rate Limit

If you hit rate limits, use a GitHub token:

```bash
export GITHUB_TOKEN=your_token_here
python scripts/fetch_discussions.py --github-token $GITHUB_TOKEN
```

### Empty Output

If cleaning produces empty output:
- Check that input file exists and is valid JSON
- Verify discussions have sufficient text content (>50 characters)
- Check that discussions are from the last 2 years

### JSON Parsing Errors

If you get JSON parsing errors:
- Ensure input file is valid JSON (not Python literals)
- Check file encoding (should be UTF-8)
- Verify file wasn't corrupted during transfer

