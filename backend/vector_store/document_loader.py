"""
Load and chunk Nextflow documentation for vector store.
"""
from typing import List, Dict
import re
import os
from pathlib import Path


def load_markdown_file(file_path: Path) -> str:
    """Load and clean markdown file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Basic cleaning: remove some markdown artifacts but keep structure
        # Remove reference-style links like {ref}`process-page`
        content = re.sub(r'\{ref\}`[^`]+`', '', content)
        # Remove page markers like (executor-page)=
        content = re.sub(r'^\([^)]+\)=\s*$', '', content, flags=re.MULTILINE)
        return content.strip()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Approximate number of tokens per chunk
        overlap: Number of tokens to overlap between chunks
    
    Returns:
        List of text chunks
    """
    # Simple token approximation (1 token ≈ 4 characters)
    char_size = chunk_size * 4
    char_overlap = overlap * 4
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + char_size
        chunk = text[start:end]
        
        # Try to break at sentence boundaries
        if end < len(text):
            # Look for sentence endings
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > char_size * 0.7:  # If we found a good break point
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - char_overlap
    
    return chunks


def load_docs_from_directory(docs_dir: str) -> List[Dict]:
    """
    Load Nextflow documentation from markdown files in a directory.
    
    Args:
        docs_dir: Path to the docs directory
    
    Returns:
        List of documents with metadata
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Warning: Docs directory not found: {docs_dir}")
        return []
    
    documents = []
    
    # Find all .md files (excluding certain directories)
    exclude_dirs = {'_static', '_templates', 'snippets', 'diagrams'}
    exclude_files = {'README.md', 'LICENCE.txt', 'conf.py', 'Makefile', 'Dockerfile', 'netlify.toml'}
    
    md_files = []
    for md_file in docs_path.rglob('*.md'):
        # Skip excluded directories
        if any(excluded in md_file.parts for excluded in exclude_dirs):
            continue
        # Skip excluded files
        if md_file.name in exclude_files:
            continue
        md_files.append(md_file)
    
    print(f"Found {len(md_files)} markdown files to process")
    
    for md_file in md_files:
        content = load_markdown_file(md_file)
        if not content or len(content) < 50:  # Skip very short files
            continue
        
        # Determine URL from file path
        # Map local path to nextflow.io docs URL
        relative_path = md_file.relative_to(docs_path)
        file_stem = md_file.stem
        
        # Build URL (approximate mapping)
        base_url = "https://www.nextflow.io/docs/latest"
        if 'developer' in str(relative_path):
            url = f"{base_url}/developer/{file_stem}.html"
        elif 'reference' in str(relative_path):
            url = f"{base_url}/reference/{file_stem}.html"
        elif 'tutorials' in str(relative_path):
            url = f"{base_url}/tutorials/{file_stem}.html"
        elif 'guides' in str(relative_path):
            url = f"{base_url}/guides/{file_stem}.html"
        elif 'migrations' in str(relative_path):
            url = f"{base_url}/migrations/{file_stem}.html"
        elif 'plugins' in str(relative_path):
            url = f"{base_url}/plugins/{file_stem}.html"
        else:
            url = f"{base_url}/{file_stem}.html"
        
        # Extract category from path
        category = 'general'
        if 'executor' in str(relative_path).lower() or 'executor' in file_stem.lower():
            category = 'executor'
        elif 'channel' in str(relative_path).lower() or 'channel' in file_stem.lower():
            category = 'channel'
        elif 'process' in str(relative_path).lower() or 'process' in file_stem.lower():
            category = 'process'
        elif 'config' in str(relative_path).lower() or 'config' in file_stem.lower():
            category = 'config'
        elif 'dsl' in str(relative_path).lower() or 'migration' in str(relative_path).lower():
            category = 'dsl'
        
        documents.append({
            'text': content,
            'metadata': {
                'source_file': str(relative_path),
                'category': category,
                'url': url,
                'title': file_stem.replace('_', ' ').title()
            }
        })
    
    print(f"Loaded {len(documents)} documents")
    return documents


def prepare_documents_for_indexing(docs_dir: str = None) -> tuple[List[str], List[dict]]:
    """
    Prepare documents for vector store indexing.
    
    Args:
        docs_dir: Path to Nextflow docs directory. If None, uses default location.
    
    Returns:
        (texts, metadata_list) tuple
    """
    if docs_dir is None:
        # Default location
        docs_dir = os.getenv("NEXTFLOW_DOCS_DIR", "/Users/nickmarveaux/Dev/nextflow/docs")
    
    docs = load_docs_from_directory(docs_dir)
    
    if not docs:
        print("Warning: No documents loaded. Using fallback knowledge base.")
        # Fallback to minimal knowledge base
        docs = [{
            'text': "The latest stable version of Nextflow is 23.10.0. Check https://github.com/nextflow-io/nextflow/releases for the most current version.",
            'metadata': {'category': 'version', 'url': 'https://github.com/nextflow-io/nextflow/releases'}
        }]
    
    texts = []
    metadata = []
    
    # Chunk documents that are too long
    chunk_size = 400  # ~400 tokens per chunk
    overlap = 50
    
    for doc in docs:
        text = doc['text']
        doc_metadata = doc['metadata']
        
        # Chunk longer documents
        if len(text) > chunk_size * 4:  # Rough estimate: 4 chars per token
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                # Add chunk index to metadata
                chunk_meta = doc_metadata.copy()
                chunk_meta['chunk_index'] = i
                chunk_meta['total_chunks'] = len(chunks)
                metadata.append(chunk_meta)
        else:
            texts.append(text)
            metadata.append(doc_metadata)
    
    print(f"Prepared {len(texts)} chunks for indexing")
    return texts, metadata

