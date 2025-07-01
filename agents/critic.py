"""
Critic – citation-verification agent
------------------------------------

Checks whether every claim in Lyra’s answer is supported by one of the
provided citations.  Uses OpenAI JSON-mode, so at least one message must
contain the word “JSON”.
"""

from __future__ import annotations

import json
import os
from typing import List

from openai import OpenAI
from app.models import LyraOutput, CriticOutput


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
