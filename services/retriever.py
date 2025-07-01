import arxiv
from typing import List, Dict
from app.models import EvidenceItem

def search_arxiv(keywords: List[str], max_results: int = 5) -> List[EvidenceItem]:
    """Search arXiv for papers matching keywords."""
    query = " AND ".join(keywords)
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    
    results = []
    for result in search.results():
        # Extract DOI from entry_id
        doi = result.entry_id.split('/')[-1]
        
        evidence_item = EvidenceItem(
            title=result.title,
            doi=doi,
            summary=result.summary[:500],  # Truncate to 500 chars
            url=result.pdf_url
        )
        results.append(evidence_item)
    
    return results 