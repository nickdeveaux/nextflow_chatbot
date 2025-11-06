#!/usr/bin/env python3
import os
import math

# --- Config ---
DOCS_DIR = os.getenv("NEXTFLOW_DOCS_DIR", "./docs")  # set to your Nextflow docs path
CHARS_PER_CHUNK = 3200  # ≈ 800 tokens per chunk

def estimate_chunks_in_file(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return math.ceil(len(text) / CHARS_PER_CHUNK)
    except Exception:
        return 0

def main():
    total_files = 0
    total_chars = 0
    total_chunks = 0
    per_ext = {}

    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if not file.endswith((".md", ".rst", ".html", ".txt")):
                continue
            total_files += 1
            path = os.path.join(root, file)
            chunks = estimate_chunks_in_file(path)
            total_chunks += chunks
            try:
                size = os.path.getsize(path)
                total_chars += size
                ext = os.path.splitext(file)[1]
                per_ext[ext] = per_ext.get(ext, 0) + 1
            except Exception:
                pass

    print(f"📘 Scanned directory: {DOCS_DIR}")
    print(f"🧾 File count: {total_files}")
    print(f"📏 Total characters: ~{total_chars:,}")
    print(f"🧩 Estimated chunks (@~{CHARS_PER_CHUNK} chars): {total_chunks:,}")
    print(f"🗂  Files by extension: {per_ext}")

if __name__ == "__main__":
    main()
