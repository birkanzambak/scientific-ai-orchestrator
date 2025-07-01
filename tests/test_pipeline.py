import pytest
from unittest.mock import Mock, patch
from app.models import SophiaOutput, NovaOutput, LyraOutput, CriticOutput, QuestionType
from agents.sophia import Sophia
from agents.nova import Nova
from agents.lyra import Lyra
from agents.critic import Critic
from app.services.retriever import search_arxiv

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
    def test_sophia_classification(self, mock_openai_client):
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices[0].message.content = '{"question_type": "factual", "keywords": ["quantum", "computing"]}'
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        sophia = Sophia()
        result = sophia.run("What is quantum computing?")
        
        assert isinstance(result, SophiaOutput)
        assert result.question_type == QuestionType.FACTUAL
        assert result.keywords == ["quantum", "computing"]

class TestNova:
    def test_nova_evidence_retrieval(self, mock_arxiv):
        # Mock arXiv results
        mock_result = Mock()
        mock_result.title = "Quantum Computing: A Survey"
        mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
        mock_result.summary = "This paper provides a comprehensive survey of quantum computing."
        mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678"
        
        mock_arxiv.results.return_value = [mock_result]
        
        sophia_output = SophiaOutput(
            question_type=QuestionType.FACTUAL,
            keywords=["quantum", "computing"]
        )
        
        nova = Nova()
        result = nova.run(sophia_output)
        
        assert isinstance(result, NovaOutput)
        assert len(result.evidence) == 1
        assert result.evidence[0].title == "Quantum Computing: A Survey"

class TestLyra:
    def test_lyra_reasoning(self, mock_openai_client):
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices[0].message.content = '''{
            "answer": "Quantum computing is a computational paradigm that uses quantum mechanical phenomena.",
            "gaps": ["Limited error correction methods"],
            "roadmap": [
                {
                    "priority": 1,
                    "research_area": "Error Correction",
                    "next_milestone": "Fault-tolerant quantum circuits",
                    "timeline": "6-12 months",
                    "success_probability": 0.65
                }
            ],
            "citations": [{"doi": "1234.5678", "idx": 1}]
        }'''
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        nova_output = NovaOutput(evidence=[])
        
        lyra = Lyra()
        result = lyra.run("What is quantum computing?", nova_output)
        
        assert isinstance(result, LyraOutput)
        assert "quantum computing" in result.answer.lower()
        assert len(result.gaps) > 0
        assert len(result.roadmap) > 0
        assert len(result.citations) > 0

class TestCritic:
    def test_critic_verification(self, mock_openai_client):
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices[0].message.content = '{"passes": true, "missing_points": []}'
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        lyra_output = LyraOutput(
            answer="Quantum computing uses qubits.",
            gaps=[],
            roadmap=[],
            citations=[]
        )
        
        critic = Critic()
        result = critic.run("What is quantum computing?", lyra_output)
        
        assert isinstance(result, CriticOutput)
        assert result.passes == True
        assert len(result.missing_points) == 0

class TestArxivRetriever:
    def test_search_arxiv(self, mock_arxiv):
        # Mock arXiv results
        mock_result = Mock()
        mock_result.title = "Test Paper"
        mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
        mock_result.summary = "Test summary"
        mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678"
        
        mock_arxiv.results.return_value = [mock_result]
        
        results = search_arxiv(["test", "keywords"])
        
        assert len(results) == 1
        assert results[0].title == "Test Paper"
        assert results[0].doi == "1234.5678"

class TestIntegration:
    def test_full_pipeline_flow(self, mock_openai_client, mock_arxiv):
        # Mock all OpenAI responses
        sophia_response = Mock()
        sophia_response.choices[0].message.content = '{"question_type": "factual", "keywords": ["test"]}'
        
        lyra_response = Mock()
        lyra_response.choices[0].message.content = '''{
            "answer": "Test answer",
            "gaps": [],
            "roadmap": [],
            "citations": []
        }'''
        
        critic_response = Mock()
        critic_response.choices[0].message.content = '{"passes": true, "missing_points": []}'
        
        mock_openai_client.chat.completions.create.side_effect = [
            sophia_response, lyra_response, critic_response
        ]
        
        # Mock arXiv
        mock_result = Mock()
        mock_result.title = "Test Paper"
        mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
        mock_result.summary = "Test summary"
        mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678"
        mock_arxiv.results.return_value = [mock_result]
        
        # Test pipeline flow
        sophia = Sophia()
        nova = Nova()
        lyra = Lyra()
        critic = Critic()
        
        question = "What is test?"
        
        # Step 1: Sophia
        sophia_output = sophia.run(question)
        assert sophia_output.question_type == QuestionType.FACTUAL
        
        # Step 2: Nova
        nova_output = nova.run(sophia_output)
        assert len(nova_output.evidence) == 1
        
        # Step 3: Lyra
        lyra_output = lyra.run(question, nova_output)
        assert "test answer" in lyra_output.answer.lower()
        
        # Step 4: Critic
        critic_output = critic.run(question, lyra_output)
        assert critic_output.passes == True 