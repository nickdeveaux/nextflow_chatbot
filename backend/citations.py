"""
Citation extraction and management.
Extracts citations from vector store search results.
"""
from typing import List, Optional, Set
from vector_store.faiss_store import FAISSVectorStore


class CitationExtractor:
    """Extracts and manages citations from vector store results."""
    
    def __init__(self, vector_store: Optional[FAISSVectorStore] = None):
        """Initialize with optional vector store."""
        self.vector_store = vector_store
    
    def extract_from_query(
        self, 
        query: str, 
        top_k: int = 3, 
        threshold: float = 0.5
    ) -> List[str]:
        """Extract citations from vector store for a query."""
        if not self.vector_store:
            return []
        
        try:
            results = self.vector_store.search(
                query, 
                top_k=top_k, 
                threshold=threshold
            )
            return self._extract_urls(results)
        except Exception:
            return []
    
    def _extract_urls(self, results: List) -> List[str]:
        """Extract unique URLs from search results."""
        seen_urls: Set[str] = set()
        citations: List[str] = []
        
        for _, _, metadata in results:
            url = metadata.get('url')
            if url and url not in seen_urls:
                citations.append(url)
                seen_urls.add(url)
        
        return citations
    
    def get_default_citations(self) -> List[str]:
        """Get default Nextflow documentation citations."""
        return [
            "https://www.nextflow.io/docs/latest/",
            "https://www.nextflow.io/docs/latest/dsl2.html",
            "https://github.com/nextflow-io/nextflow"
        ]

