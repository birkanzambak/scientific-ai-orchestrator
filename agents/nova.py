"""
Nova – evidence retriever
-------------------------

Queries arXiv (via `services.retriever.search_arxiv`) with the keywords
extracted by Sophia and returns up to `max_results` items as a
`NovaOutput`.
"""

from __future__ import annotations

from typing import List

from services.retriever import search_arxiv
from app.models import SophiaOutput, NovaOutput, EvidenceItem


class Nova:
    """Retrieve top-k relevant papers from arXiv."""

    def __init__(self, max_results: int = 5) -> None:
        self.max_results = max_results

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def run(self, sophia_output: SophiaOutput) -> NovaOutput:
        """
        Parameters
        ----------
        sophia_output : SophiaOutput
            Contains the list of keywords produced by Sophia.

        Returns
        -------
        NovaOutput
            Wraps the list of `EvidenceItem` objects.
        """
        evidence: List[EvidenceItem] = search_arxiv(
            sophia_output.keywords, max_results=self.max_results
        )

        # Fallback in the unlikely event nothing is found
        if not evidence:
            # You may choose to raise an error instead
            print("[Nova] No evidence retrieved from arXiv; continuing with empty list.")

        return NovaOutput(evidence=evidence)
