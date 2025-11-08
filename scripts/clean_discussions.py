#!/usr/bin/env python3
"""
Clean and format Nextflow discussions for vector store.

Part 2: Cleaning - Removes avatar links, user data, and formats for embeddings.
Outputs clean JSON file ready for vector store indexing.

Usage:
  python clean_discussions.py --input data/discussions/raw_discussions.json --output data/discussions/clean_discussions.json

This script:
1. Removes avatar URLs and user profile data
2. Removes unnecessary metadata
3. Formats text for embeddings
4. Adds metadata needed for vector store
"""

import json
import re
import argparse
import ast
from pathlib import Path
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def remove_avatar_urls(text: str) -> str:
    """Remove avatar URLs from text."""
    # Remove GitHub avatar URLs
    text = re.sub(r'https?://avatars\.githubusercontent\.com/[^\s\)]+', '', text)
    # Remove generic avatar URLs
    text = re.sub(r'https?://[^/]+/avatar[s]?/[^\s\)]+', '', text)
    # Remove gravatar URLs
    text = re.sub(r'https?://[^/]*gravatar[^/]*/[^\s\)]+', '', text)
    return text


def clean_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive/unnecessary user data."""
    cleaned = {}
    for key, value in data.items():
        if key in ['avatar_url', 'gravatar_id', 'user', 'author_info', 
                   'answer_author_info', 'raw_data', 'author', 'answer_author']:
            continue
        elif isinstance(value, dict):
            cleaned[key] = clean_user_data(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_user_data(item) if isinstance(item, dict) else item 
                           for item in value]
        elif isinstance(value, str):
            # Clean text content
            cleaned[key] = remove_avatar_urls(value)
        else:
            cleaned[key] = value
    return cleaned


def convert_raw_github_discussion(discussion: Dict[str, Any]) -> Dict[str, Any]:
    """Convert raw GitHub API response to our format."""
    from bs4 import BeautifulSoup
    
    # Extract body text from HTML
    body_html = discussion.get("body", "")
    body_text = BeautifulSoup(body_html or "", "html.parser").get_text(" ", strip=True)
    
    return {
        "platform": "github",
        "title": discussion.get("title", "").strip(),
        "url": discussion.get("html_url", ""),
        "body_html": body_html,
        "body_text": body_text,
        "answer_url": discussion.get("answer_html_url"),
        "created_at": discussion.get("created_at"),
        "updated_at": discussion.get("updated_at"),
        "author": discussion.get("user", {}).get("login"),
        "author_info": discussion.get("user", {}),
        "labels": discussion.get("labels", []),
        "comments": discussion.get("comments", 0),
        "category": discussion.get("category", {}),
        "raw_data": discussion
    }


def clean_discussion(discussion: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a single discussion record."""
    # Handle raw GitHub API format (convert if needed)
    if "platform" not in discussion and "html_url" in discussion:
        discussion = convert_raw_github_discussion(discussion)
    
    cleaned = {
        "platform": discussion.get("platform", "unknown"),
        "title": discussion.get("title", "").strip(),
        "url": discussion.get("url", ""),
        "created_at": discussion.get("created_at"),
        "updated_at": discussion.get("updated_at"),
    }
    
    # Extract and clean text content
    if discussion.get("platform") == "github":
        # GitHub discussions
        body_text = discussion.get("body_text", "")
        if not body_text:
            # Fallback to body_html if body_text not available
            from bs4 import BeautifulSoup
            body_html = discussion.get("body_html", discussion.get("body", ""))
            body_text = BeautifulSoup(body_html or "", "html.parser").get_text(" ", strip=True)
        
        cleaned["text"] = remove_avatar_urls(body_text).strip()
        cleaned["source"] = "GitHub Discussions"
        cleaned["license"] = "Public under GitHub ToS"
        
        # Keep answer URL if available
        if discussion.get("answer_url"):
            cleaned["answer_url"] = discussion.get("answer_url")
            
    elif discussion.get("platform") == "seqera":
        # Seqera Community
        body_text = discussion.get("body_text", "")
        cleaned["text"] = remove_avatar_urls(body_text).strip()
        cleaned["source"] = "Seqera Community"
        cleaned["license"] = "CC BY-SA 4.0"
    else:
        # Unknown format - try to extract text
        body_text = discussion.get("body_text", discussion.get("body", ""))
        cleaned["text"] = remove_avatar_urls(body_text).strip()
        cleaned["source"] = "Unknown"
        cleaned["license"] = "Unknown"
    
    # Remove empty text
    if not cleaned.get("text") or len(cleaned["text"]) < 50:
        return None
    
    # Add metadata for vector store
    cleaned["metadata"] = {
        "platform": cleaned["platform"],
        "source": cleaned.get("source", ""),
        "url": cleaned["url"],
        "title": cleaned["title"],
        "created_at": cleaned.get("created_at"),
    }
    
    return cleaned


def format_for_vector_store(discussions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format cleaned discussions for vector store indexing."""
    formatted = []
    
    for disc in discussions:
        cleaned = clean_discussion(disc)
        if not cleaned:
            continue
        
        # Format for vector store (matches document_loader.py format)
        formatted.append({
            "text": cleaned["text"],
            "metadata": cleaned["metadata"]
        })
    
    return formatted


def main():
    parser = argparse.ArgumentParser(description="Clean and format discussions for vector store")
    parser.add_argument("--input", type=str, required=True,
                       help="Input raw discussions JSON file")
    parser.add_argument("--output", type=str, required=True,
                       help="Output cleaned discussions JSON file")
    parser.add_argument("--format", choices=["vector_store", "simple"], default="vector_store",
                       help="Output format: vector_store (for indexing) or simple (cleaned only)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading discussions from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    # Try JSON first, then Python literal (eval as fallback for malformed files)
    raw_discussions = None
    try:
        raw_discussions = json.loads(content)
    except json.JSONDecodeError:
        try:
            # Try parsing as Python literal (for files like nextflow_discussions_clean.json)
            raw_discussions = ast.literal_eval(content)
        except (ValueError, SyntaxError):
            try:
                # Last resort: eval (for files that are Python literals but not valid ast)
                # This is safe because we're only loading data files we control
                raw_discussions = eval(content)
            except Exception as e:
                print(f"Error: Could not parse input file as JSON, Python literal, or eval: {e}")
                print(f"First 200 chars: {repr(content[:200])}")
                return 1
    
    if not isinstance(raw_discussions, list):
        print(f"Error: Expected list, got {type(raw_discussions)}")
        return 1
    
    print(f"Loaded {len(raw_discussions)} discussions")
    print("Cleaning discussions...")
    
    if args.format == "vector_store":
        cleaned = format_for_vector_store(raw_discussions)
    else:
        cleaned = [clean_discussion(d) for d in raw_discussions]
        cleaned = [c for c in cleaned if c is not None]
    
    print(f"Cleaned {len(cleaned)} discussions (removed {len(raw_discussions) - len(cleaned)} empty/invalid)")
    
    # Save cleaned JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(cleaned)} cleaned discussions → {output_path}")
    print(f"   Ready for vector store indexing!")
    
    return 0


if __name__ == "__main__":
    exit(main())

