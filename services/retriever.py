import arxiv
from typing import List
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
        doi = result.entry_id.split('/')[-1]
        authors = [author.name for author in result.authors] if result.authors else []
        
        evidence_item = EvidenceItem(
            title=result.title,
            doi=doi,
            summary=result.summary[:500],
            url=result.pdf_url,
            authors=authors
        )
        results.append(evidence_item)
    
    return results


def search_arxiv_and_pubmed(keywords: List[str], max_results: int = 8, topic_filter=None) -> List[EvidenceItem]:
    """Search both arXiv and PubMed. For now, just return arXiv results."""
    return search_arxiv(keywords, max_results)
