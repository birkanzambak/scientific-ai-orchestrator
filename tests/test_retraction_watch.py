"""
Tests for the retraction watch utility.
"""

import pytest
from utils.retraction_watch import (
    is_retracted,
    filter_retracted_papers,
    get_retraction_reason,
    add_retracted_doi,
    remove_retracted_doi
)


class TestRetractionWatch:
    """Test retraction watch functionality."""
    
    def test_is_retracted_with_retracted_doi(self):
        """Test that retracted DOIs are correctly identified."""
        assert is_retracted("10.1038/nature12345") == True
        assert is_retracted("10.1126/science.abc123") == True
        assert is_retracted("https://doi.org/10.1016/j.cell.2020.123") == True
    
    def test_is_retracted_with_normal_doi(self):
        """Test that normal DOIs are not flagged as retracted."""
        assert is_retracted("10.1038/nature67890") == False
        assert is_retracted("10.1126/science.def456") == False
        assert is_retracted("") == False
        assert is_retracted(None) == False
    
    def test_filter_retracted_papers(self):
        """Test filtering out retracted papers from a list."""
        papers = [
            {"doi": "10.1038/nature12345", "title": "Retracted Paper"},
            {"doi": "10.1038/nature67890", "title": "Normal Paper"},
            {"doi": "10.1126/science.abc123", "title": "Another Retracted"},
            {"doi": "10.1126/science.def456", "title": "Another Normal"}
        ]
        
        filtered = filter_retracted_papers(papers)
        
        assert len(filtered) == 2
        assert any(p["title"] == "Normal Paper" for p in filtered)
        assert any(p["title"] == "Another Normal" for p in filtered)
        assert not any(p["title"] == "Retracted Paper" for p in filtered)
        assert not any(p["title"] == "Another Retracted" for p in filtered)
    
    def test_get_retraction_reason(self):
        """Test getting retraction reasons."""
        assert get_retraction_reason("10.1038/nature12345") == "Data fabrication"
        assert get_retraction_reason("10.1126/science.abc123") == "Plagiarism"
        assert get_retraction_reason("10.1038/nature67890") == ""  # Not retracted
    
    def test_add_and_remove_retracted_doi(self):
        """Test adding and removing DOIs from the retracted list."""
        test_doi = "10.1234/test.2024"
        
        # Initially not retracted
        assert is_retracted(test_doi) == False
        
        # Add to retracted list
        add_retracted_doi(test_doi, "Test reason")
        assert is_retracted(test_doi) == True
        assert get_retraction_reason(test_doi) == "Test reason"
        
        # Remove from retracted list
        remove_retracted_doi(test_doi)
        assert is_retracted(test_doi) == False
        assert get_retraction_reason(test_doi) == ""
    
    def test_doi_normalization(self):
        """Test that DOIs are properly normalized."""
        # Test with https://doi.org/ prefix
        assert is_retracted("https://doi.org/10.1038/nature12345") == True
        
        # Test with http://doi.org/ prefix
        assert is_retracted("http://doi.org/10.1038/nature12345") == True
        
        # Test with whitespace
        assert is_retracted("  10.1038/nature12345  ") == True 