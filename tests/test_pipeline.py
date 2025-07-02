import pytest
from unittest.mock import Mock, patch
from app.models import SophiaOutput, NovaOutput, LyraOutput, CriticOutput, QuestionType, EvidenceItem, RoadmapItem, Citation
from agents.sophia import Sophia
from agents.nova import Nova
from agents.lyra import Lyra
from agents.critic import Critic
from services.retriever import search_arxiv_and_pubmed, search_arxiv

@pytest.fixture
def mock_openai_client():
    with patch('openai.OpenAI') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_arxiv():
    with patch('arxiv.Search') as mock:
        search = Mock()
        mock.return_value = search
        yield search

class TestSophia:
    @patch('agents.sophia.OpenAI')
    def test_sophia_classification(self, mock_openai_class):
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '{"question_type": "factual", "keywords": ["quantum", "computing"]}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        sophia = Sophia()
        result = sophia.run("What is quantum computing?")
        
        assert isinstance(result, SophiaOutput)
        assert result.question_type == QuestionType.FACTUAL
        assert result.keywords == ["quantum", "computing"]

class TestNova:
    @patch('agents.nova.search_arxiv_and_pubmed')
    @patch('agents.nova.Critic')
    def test_nova_evidence_retrieval(self, mock_critic_class, mock_search):
        # Mock Critic
        mock_critic = Mock()
        mock_critic_class.return_value = mock_critic
        mock_critic.run_raw.return_value = Mock(should_rerun=False, rerun_reason=None, quality_score=1.0, suggestions=[])
        
        # Mock combined search results
        mock_evidence = [
            EvidenceItem(
                title="Quantum Computing: A Survey",
                doi="1234.5678",
                summary="This paper provides a comprehensive survey of quantum computing.",
                url="http://arxiv.org/pdf/1234.5678",
                authors=["Author 1", "Author 2"]
            )
        ]
        mock_search.return_value = mock_evidence
        
        sophia_output = SophiaOutput(
            question_type=QuestionType.FACTUAL,
            keywords=["quantum", "computing"]
        )
        
        nova = Nova()
        question = "What is quantum computing?"
        result = nova.run(question, sophia_output)
        
        assert isinstance(result, NovaOutput)
        assert len(result.evidence) == 1
        assert result.evidence[0].title == "Quantum Computing: A Survey"
        assert result.critic_feedback is not None

class TestArxivRetriever:
    @patch('tests.test_pipeline.search_arxiv')
    def test_search_arxiv(self, mock_search):
        # Mock arXiv results
        mock_evidence = [
            EvidenceItem(
                title="Test Paper",
                doi="1234.5678",
                summary="Test summary",
                url="http://arxiv.org/pdf/1234.5678",
                authors=["Author 1"]
            )
        ]
        mock_search.return_value = mock_evidence
        
        results = search_arxiv(["test", "keywords"])
        
        assert len(results) == 1
        assert results[0].title == "Test Paper"
        assert results[0].doi == "1234.5678"
        
