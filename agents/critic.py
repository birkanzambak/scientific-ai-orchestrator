"""
Critic – citation-verification agent
------------------------------------

Checks whether every claim in Lyra's answer is supported by one of the
provided citations.  Uses OpenAI JSON-mode, so at least one message must
contain the word "JSON".
"""

from __future__ import annotations

import json
import os
from typing import List

from openai import OpenAI
from app.models import LyraOutput, CriticOutput, CriticFeedback, EvidenceItem


class Critic:
    """Validate that each claim in the answer is backed by a citation."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ------------------------------------------------------------------ #
    def run(self, question: str, lyra_output: LyraOutput) -> CriticOutput:
        """
        Return a CriticOutput with:
        • passes : bool
        • missing_points : list[str]
        """

        # ---------- citations block for the prompt ---------- #
        citations_text = "\n".join(
            f"- Citation {c.idx}: {c.doi}" for c in lyra_output.citations
        )

        user_msg = (
            f"QUESTION:\n{question}\n\n"
            f"ANSWER:\n{lyra_output.answer}\n\n"
            f"CITATIONS:\n{citations_text}\n\n"
            "Evaluate whether every claim is fully supported. "
            "Respond **ONLY in valid JSON** with this schema:\n"
            '{\n'
            '  "passes": true,\n'
            '  "missing_points": ["claim 1", "claim 2"]\n'
            '}'
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict citation-verification agent. "
                        "Your reply must be valid JSON; do not add commentary."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        payload: dict[str, bool | List[str]] = json.loads(
            response.choices[0].message.content
        )

        return CriticOutput(
            passes=payload["passes"],
            missing_points=payload["missing_points"],
        )

    def run_raw(self, query: str, evidence: List[EvidenceItem], agent_name: str) -> CriticFeedback:
        """
        Provide feedback on evidence quality for Nova agent.
        
        Parameters
        ----------
        query : str
            The original question
        evidence : List[EvidenceItem]
            List of evidence items to evaluate
        agent_name : str
            Name of the agent being evaluated (e.g., "Nova")
            
        Returns
        -------
        CriticFeedback
            Feedback on evidence quality and suggestions for improvement
        """
        # Build evidence summary
        evidence_summary = "\n".join([
            f"{i+1}. {item.title}\n   DOI: {item.doi or 'N/A'}\n   Summary: {item.summary[:200]}..."
            for i, item in enumerate(evidence)
        ])
        
        user_msg = (
            f"QUESTION:\n{query}\n\n"
            f"EVIDENCE FOUND BY {agent_name.upper()}:\n{evidence_summary}\n\n"
            "Evaluate the quality and relevance of this evidence for answering the question. "
            "Respond **ONLY in valid JSON** with this schema:\n"
            '{\n'
            '  "should_rerun": false,\n'
            '  "rerun_reason": "string or null",\n'
            '  "quality_score": 0.85,\n'
            '  "suggestions": ["suggestion 1", "suggestion 2"]\n'
            '}'
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a critical evidence quality assessor. "
                        "Your reply must be valid JSON; do not add commentary."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        payload = json.loads(response.choices[0].message.content)
        
        return CriticFeedback(
            should_rerun=payload.get("should_rerun", False),
            rerun_reason=payload.get("rerun_reason"),
            quality_score=payload.get("quality_score", 1.0),
            suggestions=payload.get("suggestions", [])
        )

    def run_raw_messages(self, messages: list) -> dict:
        """
        Call the Critic agent with a list of OpenAI-style messages and return the raw JSON response.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)
