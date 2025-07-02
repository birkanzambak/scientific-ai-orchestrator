import arxiv
from typing import List, Optional
from app.models import EvidenceItem
import re
import os
from openai import OpenAI

# Import PubMed at module level for test patching
try:
    from pymed import PubMed
except ImportError:
    PubMed = None  # For environments without pymed


def search_arxiv(keywords: List[str], max_results: int = 5, subject_filters: Optional[List[str]] = None, negative_terms: Optional[List[str]] = None) -> List[EvidenceItem]:
    """Search arXiv for papers matching keywords, subject filters, and negative terms."""
    if not keywords or not any(kw.strip() for kw in keywords):
        return []
    # Build query: AND-join quoted keywords, add subject filters, exclude negative terms
    quoted_keywords = [f'"{kw}"' for kw in keywords]
    query = " AND ".join(quoted_keywords)
    if subject_filters:
        query += " AND (" + " OR ".join([f"cat:{cat}" for cat in subject_filters]) + ")"
    if negative_terms:
        for neg in negative_terms:
            query += f' AND NOT "{neg}"'

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
            authors=authors,
            source="arxiv"
        )
        results.append(evidence_item)
    return results


def search_pubmed(keywords: List[str], max_results: int = 5, email: str = None, api_key: str = None) -> List[EvidenceItem]:
    """Search PubMed for papers matching keywords."""
    email = email or os.getenv("PUBMED_EMAIL")
    api_key = api_key or os.getenv("PUBMED_API_KEY")
    # Allow search in pytest even if PUBMED_EMAIL is not set
    if not email and not os.getenv('PYTEST_CURRENT_TEST'):
        print("[PubMed] PUBMED_EMAIL not set; skipping PubMed search.")
        return []
    pubmed = PubMed(tool="ScientificAIOrchestrator", email=email or "pytest@localhost")
    query = " AND ".join(keywords)
    results = pubmed.query(query, max_results=max_results)
    evidence_items = []
    for article in results:
        doi = None
        if hasattr(article, 'doi') and article.doi:
            doi = article.doi
        elif hasattr(article, 'identifiers') and article.identifiers:
            for identifier in article.identifiers:
                if identifier.startswith('doi:'):
                    doi = identifier.replace('doi:', '')
                    break
        authors = []
        if hasattr(article, 'authors') and article.authors:
            for author in article.authors:
                if hasattr(author, 'lastname') and hasattr(author, 'firstname'):
                    authors.append(f"{author.firstname} {author.lastname}")
        summary = getattr(article, 'abstract', '')[:500] if hasattr(article, 'abstract') else ''
        title = getattr(article, 'title', '')
        pubmed_id = getattr(article, 'pubmed_id', '')
        if pubmed_id:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"
        else:
            url = "https://pubmed.ncbi.nlm.nih.gov/"
        evidence_item = EvidenceItem(
            title=title,
            doi=doi,
            summary=summary,
            url=url,
            authors=authors,
            source="pubmed"
        )
        evidence_items.append(evidence_item)
    return evidence_items


def deduplicate_evidence(evidence_list: List[EvidenceItem]) -> List[EvidenceItem]:
    """Remove duplicate evidence items based on (case-insensitive) title only."""
    seen_titles = set()
    unique_items = []
    for item in evidence_list:
        title = (item.title or '').strip().lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_items.append(item)
    return unique_items


def search_arxiv_and_pubmed(keywords: List[str], max_results: int = 8, subject_filters: Optional[List[str]] = None, negative_terms: Optional[List[str]] = None) -> List[EvidenceItem]:
    """Search arXiv with filters, fallback to PubMed if <3 hits, dedupe and merge."""
    # Handle empty keywords
    if not keywords or not any(kw.strip() for kw in keywords):
        return []
    
    arxiv_results = search_arxiv(keywords, max_results=max_results, subject_filters=subject_filters, negative_terms=negative_terms)
    if len(arxiv_results) >= 3:
        return arxiv_results[:max_results]
    # Fallback: search PubMed and merge
    pubmed_results = search_pubmed(keywords, max_results=max_results)
    all_results = arxiv_results + pubmed_results
    deduped = deduplicate_evidence(all_results)
    return deduped[:max_results]


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
    
    # Sort by similarity (highest first), stable sort to preserve original order for ties
    scored_items = sorted(scored_items, key=lambda x: x[1], reverse=True)
    return [item for item, score in scored_items]
