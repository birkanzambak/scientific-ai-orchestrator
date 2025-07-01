from app.services.retriever import search_arxiv
from app.models import SophiaOutput, NovaOutput

class Nova:
    def run(self, sophia_output: SophiaOutput) -> NovaOutput:
        """Retrieve evidence from arXiv based on Sophia's keywords."""
        evidence = search_arxiv(sophia_output.keywords, max_results=5)
        return NovaOutput(evidence=evidence) 