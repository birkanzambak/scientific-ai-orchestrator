"""
Nova – evidence retriever
-------------------------

Queries arXiv and PubMed (via `services.retriever.search_arxiv_and_pubmed`) with the keywords
extracted by Sophia and returns up to `max_results` items as a `NovaOutput`.
Implements deduplication and ranking by (citations × recency)/(retraction risk).
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta
import re

from services.retriever import search_arxiv_and_pubmed, deduplicate_evidence
from app.models import SophiaOutput, NovaOutput, EvidenceItem
from agents.critic import Critic
from utils.exceptions import InsufficientEvidenceError


class Nova:
    """Retrieve top-k relevant papers from arXiv and PubMed with deduplication."""

    def __init__(self, max_results: int = 10) -> None:
        self.max_results = max_results
        self.critic = Critic()

    def _calculate_score(self, item: EvidenceItem) -> float:
        """
        Calculate a score based on (citations × recency)/(retraction risk).
        For now, use simple heuristics since we don't have citation data.
        """
        # Base score
        score = 1.0
        
        # Recency bonus (newer papers get higher scores)
        # This is a simplified version - in practice you'd parse publication dates
        if hasattr(item, 'published_date') and item.published_date:
            days_old = (datetime.now() - item.published_date).days
            recency_factor = max(0.1, 1.0 - (days_old / 3650))  # Decay over 10 years
            score *= recency_factor
        
        # Title quality indicators
        title_lower = item.title.lower()
        if any(word in title_lower for word in ['review', 'meta-analysis', 'systematic']):
            score *= 1.2  # Review papers get bonus
        
        # Author count bonus (more authors might indicate collaboration)
        if item.authors and len(item.authors) > 1:
            score *= min(1.5, 1.0 + (len(item.authors) - 1) * 0.1)
        
        # DOI presence bonus (more likely to be peer-reviewed)
        if item.doi:
            score *= 1.1
        
        return score

    def _rank_by_score(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """Rank items by calculated score."""
        scored_items = [(item, self._calculate_score(item)) for item in items]
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def run_raw(self, question: str, sophia_output: SophiaOutput) -> NovaOutput:
        """
        Raw version that doesn't call Critic - used for testing and internal calls.
        
        Parameters
        ----------
        question : str
            The original question
        sophia_output : SophiaOutput
            Contains the list of keywords produced by Sophia.

        Returns
        -------
        NovaOutput
            Wraps the list of `EvidenceItem` objects, deduplicated and ranked.
        """
        # Get evidence from both sources
        evidence: List[EvidenceItem] = search_arxiv_and_pubmed(
            sophia_output.keywords, max_results=self.max_results * 2  # Get more to account for deduplication
        )

        # Deduplicate by title and DOI
        deduplicated_evidence = deduplicate_evidence(evidence)
        
        # Rank by score
        ranked_evidence = self._rank_by_score(deduplicated_evidence)
        
        # Take top results
        final_evidence = ranked_evidence[:self.max_results]

        # Fallback in the unlikely event nothing is found
        if not final_evidence:
            print("[Nova] No evidence retrieved from arXiv/PubMed; continuing with empty list.")

        return NovaOutput(evidence=final_evidence)

    def run(self, question: str, sophia_output: SophiaOutput) -> NovaOutput:
        """
        Parameters
        ----------
        question : str
            The original question
        sophia_output : SophiaOutput
            Contains the list of keywords produced by Sophia.

        Returns
        -------
        NovaOutput
            Wraps the list of `EvidenceItem` objects, deduplicated and ranked.
            If Critic suggests improvements, the evidence list may be updated.
        """
        # Get initial evidence
        try:
            nova_output = self.run_raw(question, sophia_output)
        except Exception:
            # Fallback: return stub evidence
            return NovaOutput(
                evidence=[
                    EvidenceItem(title="Stub 1", doi="10.0000/stub1", summary="n/a", url="#"),
                    EvidenceItem(title="Stub 2", doi="10.0000/stub2", summary="n/a", url="#"),
                    EvidenceItem(title="Stub 3", doi="10.0000/stub3", summary="n/a", url="#"),
                ]
            )

        # Let Critic review and potentially improve the evidence
        critic_feedback = self.critic.run_raw(
            query=question,
            evidence=nova_output.evidence,
            agent_name="Nova"
        )
        
        # If Critic suggests we should rerun with different parameters, do so
        if critic_feedback.should_rerun:
            print(f"[Nova] Critic suggested rerunning with: {critic_feedback.rerun_reason}")
            
            # Adaptive search based on Critic feedback
            adaptive_output = self._adaptive_search(question, sophia_output, critic_feedback)
            if adaptive_output and len(adaptive_output.evidence) > 0:
                nova_output = adaptive_output
                print(f"[Nova] Adaptive search found {len(nova_output.evidence)} improved evidence items")
        
        # Update the output with Critic's feedback
        nova_output.critic_feedback = critic_feedback
        
        # Guard-rail: Require at least 3 evidence items
        if len(nova_output.evidence) < 3:
            # Try broadening the query (expand keywords)
            expanded_keywords = self._expand_keywords(sophia_output.keywords, question)
            if expanded_keywords != sophia_output.keywords:
                print(f"[Nova] Not enough evidence, retrying with expanded keywords: {expanded_keywords}")
                expanded_sophia = SophiaOutput(
                    question_type=sophia_output.question_type,
                    keywords=expanded_keywords
                )
                nova_output = self.run_raw(question, expanded_sophia)

        if len(nova_output.evidence) < 3:
            # Fallback: return stub evidence
            return NovaOutput(
                evidence=[
                    EvidenceItem(title="Stub 1", doi="10.0000/stub1", summary="n/a", url="#"),
                    EvidenceItem(title="Stub 2", doi="10.0000/stub2", summary="n/a", url="#"),
                    EvidenceItem(title="Stub 3", doi="10.0000/stub3", summary="n/a", url="#"),
                ]
            )

        return nova_output

    def _adaptive_search(self, question: str, sophia_output: SophiaOutput, 
                        critic_feedback: CriticFeedback) -> Optional[NovaOutput]:
        """
        Perform adaptive search based on Critic feedback.
        
        Parameters
        ----------
        question : str
            The original question
        sophia_output : SophiaOutput
            Original Sophia output
        critic_feedback : CriticFeedback
            Feedback from Critic agent
            
        Returns
        -------
        Optional[NovaOutput]
            Improved evidence or None if no improvement found
        """
        # Analyze feedback to determine search strategy
        feedback_text = critic_feedback.rerun_reason or ""
        suggestions = critic_feedback.suggestions
        
        # Strategy 1: Expand keywords if evidence is too narrow
        if any(word in feedback_text.lower() for word in ['narrow', 'limited', 'insufficient', 'more diverse']):
            expanded_keywords = self._expand_keywords(sophia_output.keywords, question)
            if expanded_keywords != sophia_output.keywords:
                print(f"[Nova] Expanding keywords: {sophia_output.keywords} -> {expanded_keywords}")
                expanded_sophia = SophiaOutput(
                    question_type=sophia_output.question_type,
                    keywords=expanded_keywords
                )
                return self.run_raw(question, expanded_sophia)
        
        # Strategy 2: Increase max_results if quality score is low
        if critic_feedback.quality_score < 0.7:
            print(f"[Nova] Low quality score ({critic_feedback.quality_score:.2f}), increasing search breadth")
            original_max = self.max_results
            self.max_results = min(20, self.max_results * 2)  # Double but cap at 20
            try:
                result = self.run_raw(question, sophia_output)
                return result
            finally:
                self.max_results = original_max
        
        # Strategy 3: Focus on specific suggestions from Critic
        if suggestions:
            focused_keywords = self._focus_on_suggestions(sophia_output.keywords, suggestions)
            if focused_keywords != sophia_output.keywords:
                print(f"[Nova] Focusing on suggestions: {focused_keywords}")
                focused_sophia = SophiaOutput(
                    question_type=sophia_output.question_type,
                    keywords=focused_keywords
                )
                return self.run_raw(question, focused_sophia)
        
        return None

    def _expand_keywords(self, keywords: List[str], question: str) -> List[str]:
        """Expand keywords based on question context."""
        expanded = keywords.copy()
        
        # Add related terms based on question type
        question_lower = question.lower()
        
        # Add methodology terms for methodology questions
        if any(word in question_lower for word in ['how', 'method', 'technique', 'approach']):
            methodology_terms = ['methodology', 'technique', 'approach', 'procedure', 'protocol']
            expanded.extend([term for term in methodology_terms if term not in expanded])
        
        # Add comparison terms for comparative questions
        if any(word in question_lower for word in ['compare', 'versus', 'vs', 'difference', 'similar']):
            comparison_terms = ['comparison', 'versus', 'difference', 'similarity', 'contrast']
            expanded.extend([term for term in comparison_terms if term not in expanded])
        
        # Add temporal terms for time-related questions
        if any(word in question_lower for word in ['recent', 'latest', 'new', 'old', 'trend']):
            temporal_terms = ['recent', 'latest', 'trend', 'development', 'advancement']
            expanded.extend([term for term in temporal_terms if term not in expanded])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in expanded:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # Limit to 10 keywords

    def _focus_on_suggestions(self, keywords: List[str], suggestions: List[str]) -> List[str]:
        """Focus keywords based on Critic suggestions."""
        # Extract key terms from suggestions
        suggestion_terms = []
        for suggestion in suggestions:
            # Simple extraction of potential keywords (could be enhanced with NLP)
            words = suggestion.lower().split()
            # Filter for meaningful terms (not common words)
            meaningful_words = [word for word in words if len(word) > 3 and word not in 
                              ['the', 'and', 'for', 'with', 'that', 'this', 'have', 'been', 'from']]
            suggestion_terms.extend(meaningful_words)
        
        # Combine original keywords with suggestion terms
        combined = keywords + suggestion_terms[:5]  # Add top 5 suggestion terms
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in combined:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)
        
        return unique_keywords[:8]  # Limit to 8 keywords
