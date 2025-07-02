import arxiv
from typing import List
from app.models import EvidenceItem
from pymed import PubMed
import re
import os
from openai import OpenAI


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


def search_pubmed(keywords: List[str], max_results: int = 5) -> List[EvidenceItem]:
    """Search PubMed for papers matching keywords."""
    pubmed = PubMed(tool="ScientificAIOrchestrator", email="your-email@example.com")
    
    query = " AND ".join(keywords)
    results = pubmed.query(query, max_results=max_results)
    
    evidence_items = []
    for article in results:
        # Extract DOI from various possible locations
        doi = None
        if hasattr(article, 'doi') and article.doi:
            doi = article.doi
        elif hasattr(article, 'identifiers') and article.identifiers:
            for identifier in article.identifiers:
                if identifier.startswith('doi:'):
                    doi = identifier.replace('doi:', '')
                    break
        
        # Extract authors
        authors = []
        if hasattr(article, 'authors') and article.authors:
            for author in article.authors:
                if hasattr(author, 'lastname') and hasattr(author, 'firstname'):
                    authors.append(f"{author.firstname} {author.lastname}")
        
        # Get summary/abstract
        summary = ""
        if hasattr(article, 'abstract') and article.abstract:
            summary = article.abstract[:500]
        elif hasattr(article, 'description') and article.description:
            summary = article.description[:500]
        
        # Get title
        title = ""
        if hasattr(article, 'title') and article.title:
            title = article.title
        
        # Get URL
        url = ""
        if hasattr(article, 'url') and article.url:
            url = article.url
        elif doi:
            url = f"https://doi.org/{doi}"
        
        evidence_item = EvidenceItem(
            title=title,
            doi=doi,
            summary=summary,
            url=url,
            authors=authors
        )
        evidence_items.append(evidence_item)
    
    return evidence_items


def search_arxiv_and_pubmed(keywords: List[str], max_results: int = 8, topic_filter=None) -> List[EvidenceItem]:
    """Search both arXiv and PubMed and return combined results."""
    arxiv_results = search_arxiv(keywords, max_results // 2)
    pubmed_results = search_pubmed(keywords, max_results // 2)
    
    # Combine results
    all_results = arxiv_results + pubmed_results
    return all_results


def deduplicate_evidence(evidence_list: List[EvidenceItem]) -> List[EvidenceItem]:
    """Remove duplicate evidence items based on title and DOI."""
    seen_titles = set()
    seen_dois = set()
    deduplicated = []
    
    for item in evidence_list:
        # Check if we've seen this title or DOI before
        title_lower = item.title.lower().strip() if item.title else ""
        doi_normalized = item.doi.strip() if item.doi else ""
        
        if title_lower not in seen_titles and doi_normalized not in seen_dois:
            seen_titles.add(title_lower)
            if doi_normalized:
                seen_dois.add(doi_normalized)
            deduplicated.append(item)
    
    return deduplicated


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length")
    
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def get_embedding(text: str, client: OpenAI) -> List[float]:
    """Get embedding for text using OpenAI API."""
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding


def rerank_by_embedding(items: List[EvidenceItem], query: str, client: OpenAI) -> List[EvidenceItem]:
    """Rerank evidence items by embedding similarity to query."""
    if not items:
        return items
    
    # Get query embedding
    query_embedding = get_embedding(query, client)
    
    # Calculate similarities
    scored_items = []
    for item in items:
        # Use title + summary for embedding
        item_text = f"{item.title} {item.summary}"
        item_embedding = get_embedding(item_text, client)
        similarity = cosine_similarity(query_embedding, item_embedding)
        scored_items.append((item, similarity))
    
    # Sort by similarity (highest first)
    scored_items.sort(key=lambda x: x[1], reverse=True)
    
    return [item for item, score in scored_items]
