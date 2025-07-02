"""
Retraction Watch Utility
------------------------

Provides functionality to filter out retracted papers based on DOI.
Uses a small mocked list of retracted DOIs for demonstration.
In production, this would connect to the Retraction Watch API or database.
"""

from typing import List, Set, Dict
import re


# Mocked list of retracted DOIs
# In production, this would be fetched from Retraction Watch API
RETRACTED_DOIS: Set[str] = {
    "10.1038/nature12345",  # Example retracted paper
    "10.1126/science.abc123",  # Another example
    "10.1016/j.cell.2020.123",  # Cell retraction
    "10.1073/pnas.123456789",  # PNAS retraction
    "10.1002/anie.202012345",  # Angewandte retraction
}

# Mocked retraction reasons
RETRACTION_REASONS: Dict[str, str] = {
    "10.1038/nature12345": "Data fabrication",
    "10.1126/science.abc123": "Plagiarism",
    "10.1016/j.cell.2020.123": "Statistical errors",
    "10.1073/pnas.123456789": "Image manipulation",
    "10.1002/anie.202012345": "Author misconduct"
}


def is_retracted(doi: str) -> bool:
    """
    Check if a paper is retracted based on its DOI.
    
    Parameters
    ----------
    doi : str
        The DOI to check
        
    Returns
    -------
    bool
        True if the paper is retracted, False otherwise
    """
    if not doi:
        return False
    
    # Normalize DOI (remove any prefixes)
    normalized_doi = re.sub(r'^https?://doi\.org/', '', doi.strip())
    
    return normalized_doi in RETRACTED_DOIS


def filter_retracted_papers(papers: List[dict]) -> List[dict]:
    """
    Filter out retracted papers from a list of paper dictionaries.
    
    Parameters
    ----------
    papers : List[dict]
        List of paper dictionaries, each containing a 'doi' field
        
    Returns
    -------
    List[dict]
        List with retracted papers removed
    """
    return [paper for paper in papers if not is_retracted(paper.get('doi', ''))]


def get_retraction_reason(doi: str) -> str:
    """
    Get the reason for retraction for a given DOI.
    
    Parameters
    ----------
    doi : str
        The DOI to check
        
    Returns
    -------
    str
        Reason for retraction, or empty string if not retracted
    """
    if not is_retracted(doi):
        return ""
    
    normalized_doi = re.sub(r'^https?://doi\.org/', '', doi.strip())
    return RETRACTION_REASONS.get(normalized_doi, "Unknown reason")


def add_retracted_doi(doi: str, reason: str = "Unknown reason") -> None:
    """
    Add a DOI to the retracted list (for testing purposes).
    
    Parameters
    ----------
    doi : str
        The DOI to add
    reason : str
        Reason for retraction
    """
    global RETRACTED_DOIS, RETRACTION_REASONS
    normalized_doi = re.sub(r'^https?://doi\.org/', '', doi.strip())
    RETRACTED_DOIS.add(normalized_doi)
    RETRACTION_REASONS[normalized_doi] = reason


def remove_retracted_doi(doi: str) -> None:
    """
    Remove a DOI from the retracted list (for testing purposes).
    
    Parameters
    ----------
    doi : str
        The DOI to remove
    """
    global RETRACTED_DOIS, RETRACTION_REASONS
    normalized_doi = re.sub(r'^https?://doi\.org/', '', doi.strip())
    RETRACTED_DOIS.discard(normalized_doi)
    RETRACTION_REASONS.pop(normalized_doi, None) 