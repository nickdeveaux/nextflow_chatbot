"""
Context formatting utilities for vector search results.
"""
from typing import List


def format_context(results: List) -> str:
    """Format search results into context string."""
    context_parts = []
    seen_urls = set()
    
    for result in results:
        # Handle tuple format: (text, similarity, metadata)
        if isinstance(result, tuple) and len(result) >= 3:
            text, _, metadata = result[:3]
        else:
            continue
        
        # Ensure metadata is a dict
        if not isinstance(metadata, dict):
            metadata = {}
        
        context_parts.append(text)
        url = metadata.get('url')
        if url and url not in seen_urls:
            context_parts.append(f"Source: {url}")
            seen_urls.add(url)
    
    return "\n\n".join(context_parts)

