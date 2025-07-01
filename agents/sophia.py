"""
Sophia – universal question classifier
--------------------------------------

Given a natural-language question, classify its type and extract
keywords.  The OpenAI response is requested in *JSON mode*, so the
system/user messages must literally contain the word “JSON”.
"""

from __future__ import annotations

import json
import os
from typing import List

from openai import OpenAI
from app.models import SophiaOutput, QuestionType


class Sophia:
    """Classify a research question and pull out key terms."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self, question: str) -> SophiaOutput:
        """
        Parameters
        ----------
        question : str
            The natural-language question submitted by the user.

        Returns
        -------
        SophiaOutput
            Dataclass / Pydantic model containing a `question_type`
            Enum and a list of `keywords`.
        """

        # ----------------------------- messages --------------------------- #
        user_prompt = (
            "You are Sophia, a universal question classifier.\n\n"
            f"QUESTION: {question}\n\n"
            "Respond in STRICT JSON ONLY:\n"
            "{\n"
            '  "question_type": "factual|causal|comparative|mechanism|prediction",\n'
            '  "keywords": ["...", "..."]\n'
            "}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0,  # deterministic classification
        )

        # ----------------------------- parsing ---------------------------- #
        try:
            payload: dict[str, str | List[str]] = json.loads(
                response.choices[0].message.content
            )
            return SophiaOutput(
                question_type=QuestionType(payload["question_type"]),
                keywords=payload["keywords"],
            )
        except Exception as exc:  # noqa: BLE001
            # Let the caller decide what to do (fail fast in Celery task)
            raise ValueError(
                f"Sophia could not parse JSON: {response.choices[0].message.content}"
            ) from exc
