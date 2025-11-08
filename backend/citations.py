"""
Citation extraction and management.
Extracts citations from vector store search results.
"""
from typing import List, Optional, Set, TYPE_CHECKING
import config

if TYPE_CHECKING:
    from vector_store.faiss_store import FAISSVectorStore

# Optional import - graceful degradation if vector store not available
try:
    from vector_store.faiss_store import FAISSVectorStore
except ImportError:
    FAISSVectorStore = None


class CitationExtractor:
    """Extracts and manages citations from vector store results."""
    
    def __init__(self, vector_store: Optional['FAISSVectorStore'] = None):
        """Initialize with optional vector store."""
        self.vector_store = vector_store
    
    def extract_from_query(
        self, 
        query: str, 
        top_k: Optional[int] = None, 
        threshold: Optional[float] = None
    ) -> List[str]:
        """Extract citations from vector store for a query."""
        if not self.vector_store:
            return []
        
        top_k = top_k or config.VECTOR_SEARCH_TOP_K
        threshold = threshold or config.VECTOR_SEARCH_THRESHOLD
        
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
        
        for result in results:
            # Handle tuple format: (text, similarity, metadata)
            if isinstance(result, tuple) and len(result) >= 3:
                _, _, metadata = result[:3]
            elif isinstance(result, dict):
                metadata = result
            else:
                continue
            
            # Ensure metadata is a dict
            if not isinstance(metadata, dict):
                continue
                
            url = metadata.get('url')
            if url and url not in seen_urls:
                citations.append(url)
                seen_urls.add(url)
        
        return citations
    
    def get_default_citations(self) -> List[str]:
        """Get default Nextflow documentation citations."""
        return getattr(config, 'DEFAULT_CITATIONS', [])

