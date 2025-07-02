import pytest
from unittest.mock import Mock, patch
from agents.nova import Nova
from app.models import SophiaOutput, EvidenceItem, QuestionType
from utils.exceptions import InsufficientEvidenceError


class TestNovaDeduplication:
    """Test Nova's deduplication functionality."""
    
    @patch('agents.nova.search_arxiv_and_pubmed')
    @patch('services.retriever.deduplicate_evidence')
    def test_nova_deduplicates_results(self, mock_deduplicate, mock_search):
        """Test that Nova deduplicates results from both sources."""
        # Mock search results with duplicates
        duplicate_item1 = EvidenceItem(
            title="Same Paper Title",
            doi="10.1234/same.2024",
            summary="First version",
            url="https://arxiv.org/abs/1234.5678",
            authors=["Author 1"],
            source="arxiv"
        )
        duplicate_item2 = EvidenceItem(
            title="Same Paper Title",  # Same title
            doi="10.1234/same.2024",   # Same DOI
            summary="Second version",
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            authors=["Author 1"],
            source="pubmed"
        )
        unique_item = EvidenceItem(
            title="Different Paper",
            doi="10.1234/different.2024",
            summary="Unique paper",
            url="https://arxiv.org/abs/5678.9012",
            authors=["Author 2"],
            source="arxiv"
        )
        
        mock_search.return_value = [duplicate_item1, duplicate_item2, unique_item]
        
        # Mock deduplication to return only unique items
        mock_deduplicate.return_value = [duplicate_item1, unique_item]
        
        nova = Nova(max_results=5)
        question = "What is quantum computing?"
        sophia_output = SophiaOutput(question_type=QuestionType.FACTUAL, keywords=["quantum", "computing"])
        
        # Should raise InsufficientEvidenceError because deduplication reduces to < 3 items
        with pytest.raises(InsufficientEvidenceError):
            result = nova.run(question, sophia_output)
    
    @patch('agents.nova.search_arxiv_and_pubmed')
    def test_nova_ranking_by_score(self, mock_search):
        """Test that Nova ranks results by calculated score."""
        # Create items with different characteristics
        review_paper = EvidenceItem(
            title="Systematic Review of Machine Learning",
            doi="10.1234/review.2024",
            summary="A comprehensive review",
            url="https://arxiv.org/abs/review.2024",
            authors=["Author 1", "Author 2", "Author 3"],
            source="arxiv"
        )
        regular_paper = EvidenceItem(
            title="Regular Research Paper",
            doi="10.1234/regular.2024",
            summary="A regular paper",
            url="https://arxiv.org/abs/regular.2024",
            authors=["Single Author"],
            source="arxiv"
        )
        third_paper = EvidenceItem(
            title="Another Research Paper",
            doi="10.1234/another.2024",
            summary="Another paper",
            url="https://arxiv.org/abs/another.2024",
            authors=["Another Author"],
            source="arxiv"
        )
        
        mock_search.return_value = [regular_paper, review_paper, third_paper]
        
        nova = Nova(max_results=5)
        question = "What is quantum computing?"
        sophia_output = SophiaOutput(question_type=QuestionType.FACTUAL, keywords=["quantum", "computing"])
        
        result = nova.run(question, sophia_output)
        
        # The review paper should be ranked higher due to:
        # - "review" in title (1.2x bonus)
        # - Multiple authors (1.2x bonus)
        # - DOI presence (1.1x bonus)
        # So it should come first
        assert result.evidence[0].title == "Systematic Review of Machine Learning"
        assert len(result.evidence) == 3
    
    @patch('agents.nova.search_arxiv_and_pubmed')
    def test_nova_respects_max_results(self, mock_search):
        """Test that Nova respects the max_results parameter."""
        # Create more items than max_results
        items = []
        for i in range(15):
            item = EvidenceItem(
                title=f"Paper {i}",
                doi=f"10.1234/paper{i}.2024",
                summary=f"Summary {i}",
                url=f"https://arxiv.org/abs/paper{i}",
                authors=[f"Author {i}"],
                source="arxiv"
            )
            items.append(item)
        
        mock_search.return_value = items
        
        nova = Nova(max_results=5)
        question = "What is quantum computing?"
        sophia_output = SophiaOutput(question_type=QuestionType.FACTUAL, keywords=["quantum", "computing"])
        
        result = nova.run(question, sophia_output)
        
        # Should only return max_results items (but Nova requires at least 3)
        assert len(result.evidence) == 5 