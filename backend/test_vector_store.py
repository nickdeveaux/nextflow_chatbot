"""
Tests for vector store functionality.
"""
import pytest
import numpy as np
import tempfile
import os
from vector_store.embeddings import EmbeddingGenerator
from vector_store.faiss_store import FAISSVectorStore


@pytest.fixture
def embedding_gen():
    """Create embedding generator for tests."""
    return EmbeddingGenerator()


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        "Nextflow is a workflow management system.",
        "DSL2 is the new syntax for Nextflow.",
        "Channels are used to pass data between processes.",
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return [
        {"url": "https://nextflow.io/docs/", "source": "docs"},
        {"url": "https://nextflow.io/docs/dsl2.html", "source": "docs"},
        {"url": "https://nextflow.io/docs/channels.html", "source": "docs"},
    ]


def test_faiss_store_initialization(embedding_gen):
    """Test FAISS store initialization."""
    store = FAISSVectorStore(embedding_gen)
    assert store.embedding_generator == embedding_gen
    assert store.index is None
    assert store.documents == []
    assert store.metadata == []


def test_faiss_store_build_index(embedding_gen, sample_documents, sample_metadata):
    """Test building an index."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(sample_documents, sample_metadata)
    
    assert store.index is not None
    assert store.index.ntotal == len(sample_documents)
    assert len(store.documents) == len(sample_documents)
    assert len(store.metadata) == len(sample_metadata)


def test_faiss_store_build_index_no_metadata(embedding_gen, sample_documents):
    """Test building an index without metadata."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(sample_documents)
    
    assert store.index is not None
    assert store.index.ntotal == len(sample_documents)
    assert len(store.documents) == len(sample_documents)
    assert len(store.metadata) == len(sample_documents)
    # All metadata should be empty dicts
    assert all(isinstance(m, dict) for m in store.metadata)


def test_faiss_store_search(embedding_gen, sample_documents, sample_metadata):
    """Test searching the index."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(sample_documents, sample_metadata)
    
    results = store.search("Nextflow workflow", top_k=2)
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= 2
    
    # Check result format: (text, similarity, metadata)
    for result in results:
        assert isinstance(result, tuple)
        assert len(result) == 3
        text, similarity, metadata = result
        
        assert isinstance(text, str)
        assert isinstance(similarity, float)
        assert isinstance(metadata, dict)
        assert 0.0 <= similarity <= 1.0


def test_faiss_store_search_empty_index(embedding_gen):
    """Test searching an empty index."""
    store = FAISSVectorStore(embedding_gen)
    results = store.search("test query")
    assert results == []


def test_faiss_store_search_threshold(embedding_gen, sample_documents, sample_metadata):
    """Test search with threshold filtering."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(sample_documents, sample_metadata)
    
    # High threshold should return fewer results
    results_high = store.search("Nextflow", top_k=10, threshold=0.9)
    results_low = store.search("Nextflow", top_k=10, threshold=0.0)
    
    assert len(results_high) <= len(results_low)
    # All results should meet threshold
    for _, similarity, _ in results_high:
        assert similarity >= 0.9


def test_faiss_store_save_and_load(embedding_gen, sample_documents, sample_metadata):
    """Test saving and loading index."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test_index.index")
        
        # Build and save
        store1 = FAISSVectorStore(embedding_gen, index_path=index_path)
        store1.build_index(sample_documents, sample_metadata)
        
        # Load into new store
        store2 = FAISSVectorStore(embedding_gen, index_path=index_path)
        store2.load(index_path)
        
        assert store2.index is not None
        assert store2.index.ntotal == store1.index.ntotal
        assert len(store2.documents) == len(store1.documents)
        assert len(store2.metadata) == len(store1.metadata)
        
        # Search should work the same
        results1 = store1.search("Nextflow")
        results2 = store2.search("Nextflow")
        
        assert len(results1) == len(results2)
        # Results should have same format
        for result in results2:
            assert isinstance(result, tuple)
            assert len(result) == 3


def test_faiss_store_metadata_access(embedding_gen, sample_documents, sample_metadata):
    """Test that metadata is properly accessible in search results."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(sample_documents, sample_metadata)
    
    results = store.search("Nextflow", top_k=3)
    
    for text, similarity, metadata in results:
        assert isinstance(metadata, dict)
        # Check that we can access URL if it exists
        if 'url' in metadata:
            assert isinstance(metadata['url'], str)


def test_faiss_store_metadata_mismatch(embedding_gen):
    """Test handling when metadata list is shorter than documents."""
    documents = ["doc1", "doc2", "doc3"]
    metadata = [{"url": "url1"}]  # Only one metadata entry
    
    store = FAISSVectorStore(embedding_gen)
    store.build_index(documents, metadata)
    
    # Should handle gracefully - metadata should be padded or handled
    results = store.search("doc", top_k=3)
    
    # All results should have valid format
    for result in results:
        assert isinstance(result, tuple)
        assert len(result) == 3
        text, similarity, meta = result
        assert isinstance(meta, dict)


def test_faiss_store_single_result(embedding_gen):
    """Test search when there's only one document."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(["Only one document"], [{"url": "test"}])
    
    results = store.search("document", top_k=1)
    
    assert len(results) == 1
    text, similarity, metadata = results[0]
    assert isinstance(text, str)
    assert isinstance(similarity, float)
    assert isinstance(metadata, dict)


def test_faiss_store_add_documents(embedding_gen, sample_documents, sample_metadata):
    """Test adding documents to existing index."""
    store = FAISSVectorStore(embedding_gen)
    store.build_index(sample_documents[:2], sample_metadata[:2])
    
    initial_count = store.index.ntotal
    
    store.add_documents(
        [sample_documents[2]], 
        [sample_metadata[2]]
    )
    
    assert store.index.ntotal == initial_count + 1
    assert len(store.documents) == initial_count + 1
    assert len(store.metadata) == initial_count + 1

