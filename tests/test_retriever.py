"""
Tests for the retriever module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.retriever import (
    search_arxiv, 
    search_pubmed, 
    search_arxiv_and_pubmed,
    deduplicate_evidence,
    rerank_by_embedding,
    get_embedding,
    cosine_similarity
)
from app.models import EvidenceItem


class TestArxivSearch:
    """Test arXiv search functionality."""
    
    @patch('services.retriever.arxiv.Search')
    def test_search_arxiv_returns_evidence_items(self, mock_search):
        """Test that search_arxiv returns EvidenceItem objects."""
        # Mock arXiv result
        mock_result = Mock()
        mock_result.title = "Test Paper"
        mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
        mock_result.summary = "This is a test paper about machine learning."
        mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678"
        mock_author1 = Mock()
        mock_author1.name = "John Doe"
        mock_author2 = Mock()
        mock_author2.name = "Jane Smith"
        mock_result.authors = [mock_author1, mock_author2]
        
        mock_search.return_value.results.return_value = [mock_result]
        
        results = search_arxiv(["machine learning"], max_results=1)
        
        assert len(results) == 1
        assert isinstance(results[0], EvidenceItem)
        assert results[0].title == "Test Paper"
        assert results[0].doi == "1234.5678"
        assert results[0].authors == ["John Doe", "Jane Smith"]


class TestPubMedSearch:
    """Test PubMed search functionality."""
    
    @patch('services.retriever.PubMed')
    def test_search_pubmed_returns_evidence_items(self, mock_pubmed_class):
        """Test that search_pubmed returns EvidenceItem objects."""
        # Mock PubMed article
        mock_article = Mock()
        mock_article.title = "Test Medical Paper"
        mock_article.doi = "10.1234/test.2024"
        mock_article.abstract = "This is a test medical paper about cancer treatment."
        mock_article.pubmed_id = "12345678"
        mock_article.url = "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        mock_article.authors = [
            Mock(lastname="Smith", firstname="John"),
            Mock(lastname="Doe", firstname="Jane")
        ]
        
        mock_pubmed = Mock()
        mock_pubmed.query.return_value = [mock_article]
        mock_pubmed_class.return_value = mock_pubmed
        
        results = search_pubmed(["cancer", "treatment"], max_results=1)
        
        assert len(results) == 1
        assert isinstance(results[0], EvidenceItem)
        assert results[0].title == "Test Medical Paper"
        assert results[0].doi == "10.1234/test.2024"
        assert results[0].authors == ["John Smith", "Jane Doe"]


class TestCombinedSearch:
    """Test combined arXiv and PubMed search."""
    
    @patch('services.retriever.search_arxiv')
    @patch('services.retriever.search_pubmed')
    def test_search_arxiv_and_pubmed_combines_results(self, mock_pubmed, mock_arxiv):
        """Test that search_arxiv_and_pubmed combines results from both sources."""
        # Mock arXiv results
        arxiv_item = EvidenceItem(
            title="ArXiv Paper",
            doi="1234.5678",
            summary="ArXiv summary",
            url="http://arxiv.org/pdf/1234.5678",
            authors=["ArXiv Author"]
        )
        mock_arxiv.return_value = [arxiv_item]
        
        # Mock PubMed results
        pubmed_item = EvidenceItem(
            title="PubMed Paper",
            doi="10.1234/pubmed.2024",
            summary="PubMed summary",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            authors=["PubMed Author"]
        )
        mock_pubmed.return_value = [pubmed_item]
        
        results = search_arxiv_and_pubmed(["quantum computing"], max_results=4)
        
        assert len(results) == 2
        assert any(item.title == "ArXiv Paper" for item in results)
        assert any(item.title == "PubMed Paper" for item in results)
        assert all(hasattr(item, 'authors') for item in results)


class TestDeduplication:
    """Test evidence deduplication functionality."""
    
    def test_deduplicate_evidence_removes_duplicates(self):
        """Test that deduplicate_evidence removes items with same title."""
        item1 = EvidenceItem(
            title="Same Title",
            doi="doi1",
            summary="summary1",
            url="url1",
            authors=["Author1"]
        )
        item2 = EvidenceItem(
            title="Same Title",
            doi="doi2",
            summary="summary2",
            url="url2",
            authors=["Author2"]
        )
        item3 = EvidenceItem(
            title="Different Title",
            doi="doi3",
            summary="summary3",
            url="url3",
            authors=["Author3"]
        )
        
        items = [item1, item2, item3]
        deduplicated = deduplicate_evidence(items)
        
        assert len(deduplicated) == 2
        assert any(item.title == "Same Title" for item in deduplicated)
        assert any(item.title == "Different Title" for item in deduplicated)


class TestEmbeddingFunctions:
    """Test embedding-related functions."""
    
    def test_cosine_similarity_calculation(self):
        """Test cosine similarity calculation."""
        a = [1, 0, 0]
        b = [0, 1, 0]
        c = [1, 0, 0]
        
        # Orthogonal vectors should have similarity 0
        assert cosine_similarity(a, b) == 0.0
        
        # Same vectors should have similarity 1
        assert cosine_similarity(a, c) == 1.0
    
    @patch('services.retriever.OpenAI')
    def test_get_embedding_returns_vector(self, mock_openai_class):
        """Test that get_embedding returns a vector."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        embedding = get_embedding("test text", mock_client)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]
    
    @patch('services.retriever.get_embedding')
    def test_rerank_by_embedding_returns_sorted_list(self, mock_get_embedding):
        """Test that rerank_by_embedding returns sorted list."""
        # Mock embeddings with explicit call tracking
        call_count = 0
        def mock_embedding_side_effect(text, client):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # Query embedding
                return [1, 0, 0]
            elif call_count == 2:  # Item1 embedding (high similarity)
                return [0.9, 0.1, 0]
            elif call_count == 3:  # Item2 embedding (low similarity)
                return [0.1, 0.9, 0]
            else:
                return [0, 0, 1]  # Fallback
        
        mock_get_embedding.side_effect = mock_embedding_side_effect
        
        mock_client = Mock()
        item1 = EvidenceItem(
            title="Item1",
            doi="doi1",
            summary="summary1",
            url="url1",
            authors=[]
        )
        item2 = EvidenceItem(
            title="Item2",
            doi="doi2",
            summary="summary2",
            url="url2",
            authors=[]
        )
        
        items = [item2, item1]  # Reverse order
        reranked = rerank_by_embedding(items, "test query", mock_client)
        
        # Should be sorted by similarity (item1 should come first)
        assert reranked[0].title == "Item1"
        assert reranked[1].title == "Item2"


class TestIntegration:
    """Integration tests for the retriever module."""
    
    @patch('services.retriever.search_arxiv')
    @patch('services.retriever.search_pubmed')
    @patch.dict('os.environ', {'OPENAI_EMBEDDING_MODEL': 'text-embedding-3-small'})
    @patch('services.retriever.OpenAI')
    def test_full_pipeline_with_embedding_reranking(self, mock_openai_class, mock_pubmed, mock_arxiv):
        """Test the full pipeline with embedding reranking enabled."""
        # Mock search results
        arxiv_item = EvidenceItem(
            title="ArXiv Paper",
            doi="doi1",
            summary="summary1",
            url="url1",
            authors=["Author1"]
        )
        pubmed_item = EvidenceItem(
            title="PubMed Paper",
            doi="doi2",
            summary="summary2",
            url="url2",
            authors=["Author2"]
        )
        
        mock_arxiv.return_value = [arxiv_item]
        mock_pubmed.return_value = [pubmed_item]
        
        # Mock embedding client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock embedding responses
        mock_client.embeddings.create.return_value.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        
        # Test the combined search
        results = search_arxiv_and_pubmed(["test"], max_results=4)
        
        assert len(results) == 2
        assert any(item.title == "ArXiv Paper" for item in results)
        assert any(item.title == "PubMed Paper" for item in results)


class MockPubMedArticle:
    def __init__(self, title, abstract, doi, authors=None, url=None):
        self.title = title
        self.abstract = abstract
        self.doi = doi
        self.authors = authors or []
        self.url = url
        self.identifiers = [f"doi:{doi}"] if doi else []


class MockAuthor:
    def __init__(self, firstname, lastname):
        self.firstname = firstname
        self.lastname = lastname


def test_search_pubmed_mocked():
    """Test PubMed search with mocked response."""
    # Mock PubMed article
    mock_article = MockPubMedArticle(
        title="Test Research Paper",
        abstract="This is a test abstract with important findings about cancer treatment.",
        doi="10.1234/test.2024.001",
        authors=[MockAuthor("John", "Doe"), MockAuthor("Jane", "Smith")],
        url="https://pubmed.ncbi.nlm.nih.gov/12345678/"
    )
    
    # Mock PubMed client
    mock_pubmed = Mock()
    mock_pubmed.query.return_value = [mock_article]
    
    with patch('services.retriever.PubMed', return_value=mock_pubmed):
        results = search_pubmed(["cancer", "treatment"], max_results=1)
    
    assert len(results) == 1
    result = results[0]
    assert result.title == "Test Research Paper"
    assert result.doi == "10.1234/test.2024.001"
    assert result.summary == "This is a test abstract with important findings about cancer treatment."
    assert result.url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    assert result.authors == ["John Doe", "Jane Smith"]


def test_search_pubmed_no_doi():
    """Test PubMed search with article that has no DOI."""
    mock_article = MockPubMedArticle(
        title="Test Paper Without DOI",
        abstract="This paper has no DOI.",
        doi=None,
        authors=[MockAuthor("Alice", "Johnson")]
    )
    
    mock_pubmed = Mock()
    mock_pubmed.query.return_value = [mock_article]
    
    with patch('services.retriever.PubMed', return_value=mock_pubmed):
        results = search_pubmed(["test"], max_results=1)
    
    assert len(results) == 1
    result = results[0]
    assert result.title == "Test Paper Without DOI"
    assert result.doi is None
    assert result.authors == ["Alice Johnson"]


def test_search_arxiv_and_pubmed_combined():
    """Test that both arXiv and PubMed results are combined."""
    # Mock arXiv result
    mock_arxiv_result = EvidenceItem(
        title="arXiv Paper",
        doi="10.1234/arxiv.2024.001",
        summary="arXiv abstract",
        url="https://arxiv.org/abs/2024.001",
        authors=["Author 1", "Author 2"]
    )
    
    # Mock PubMed result
    mock_pubmed_result = EvidenceItem(
        title="PubMed Paper",
        doi="10.1234/pubmed.2024.001",
        summary="PubMed abstract",
        url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        authors=["Author 3", "Author 4"]
    )
    
    with patch('services.retriever.search_arxiv', return_value=[mock_arxiv_result]), \
         patch('services.retriever.search_pubmed', return_value=[mock_pubmed_result]):
        results = search_arxiv_and_pubmed(["test"], max_results=4)
    
    assert len(results) == 2
    assert results[0].title == "arXiv Paper"
    assert results[1].title == "PubMed Paper" 