import pytest
from agents.dataminer import DataMiner
from app.models import EvidenceItem
from unittest.mock import patch, Mock


def test_dataminer_regex_extract_percentage():
    abstract = "In this study, 31 % of patients responded to treatment."
    evidence = EvidenceItem(
        title="Test Paper",
        doi="10.1234/test.2024",
        summary=abstract,
        url="https://example.com",
        authors=["Author 1"],
        source="arxiv"
    )
    miner = DataMiner()
    result = miner.regex_extract(abstract)
    assert "31 %" in result.percentages


def test_dataminer_openai_extract_percentage():
    abstract = "In this study, 31 % of patients responded to treatment."
    evidence = EvidenceItem(
        title="Test Paper",
        doi="10.1234/test.2024",
        summary=abstract,
        url="https://example.com",
        authors=["Author 1"],
        source="arxiv"
    )
    miner = DataMiner()
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"percentages": ["31 %"], "p_values": [], "confidence_intervals": [], "sample_sizes": []}'))]
    with patch.object(miner.client.chat.completions, 'create', return_value=mock_response):
        result = miner.run(evidence)
    assert "31 %" in result.percentages 