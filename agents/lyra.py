"""
Lyra – scientific reasoning agent
---------------------------------

Takes a research question + evidence (Nova’s output) and produces
• an evidence-based answer
• remaining knowledge gaps
• a short research roadmap
• citation links (idx ties back to evidence array)

The reply is requested in *JSON mode*, so at least one user/system
message must literally contain the word “JSON”.
"""

from __future__ import annotations

import json
import os
from typing import List

from openai import OpenAI
from app.models import NovaOutput, LyraOutput, RoadmapItem, Citation


class Lyra:
    """Reason over evidence and craft a research-grade answer."""

    # ------------------------------ config ------------------------------ #
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.cost_threshold = float(os.getenv("COST_THRESHOLD_USD", "0.05"))

    # ------------------------ token/cost helpers ------------------------ #
    @staticmethod
    def _rough_tokens(text: str) -> int:
        """Very rough ≈4 chars / token heuristic (good enough for guard-rails)."""
        return max(1, len(text) // 4)

    @staticmethod
    def _estimate_cost(in_toks: int, out_toks: int, model: str) -> float:
        """
        Return cost in USD using OpenAI June 2024 price table.

        (If `model` isn’t known we fall back to the mini tier.)
        """
        price = {
            "gpt-4o": {"in": 0.0025, "out": 0.01},          # per 1 k tokens
            "gpt-4o-mini": {"in": 0.00015, "out": 0.0006},
        }.get(model, {"in": 0.00015, "out": 0.0006})

        return (in_toks / 1_000) * price["in"] + (out_toks / 1_000) * price["out"]

    # ----------------------------- runner ------------------------------ #
    def run(
        self,
        question: str,
        nova_output: NovaOutput,
        critique: dict | None = None,
    ) -> LyraOutput:
        """Main entry point – returns a fully-typed `LyraOutput`."""

        # ---------- build evidence & optional critique strings ---------- #
        evidence_lines: List[str] = []
        for idx, item in enumerate(nova_output.evidence, 1):
            evidence_lines.append(
                f"{idx}. {item.title}\n"
                f"   DOI: {item.doi}\n"
                f"   Summary: {item.summary}"
            )
        evidence_block = "\n\n".join(evidence_lines)

        critique_block = ""
        if critique:
            critique_block = (
                "\n\nPrior critique flagged missing points:\n"
                + "\n".join(f"- {pt}" for pt in critique.get("missing_points", []))
            )

        # ------------------------ prompt assembly ----------------------- #
        json_schema = (
            '{\n'
            '  "answer": "string",\n'
            '  "gaps": ["string", ...],\n'
            '  "roadmap": [\n'
            '    {\n'
            '      "priority": 1,\n'
            '      "research_area": "string",\n'
            '      "next_milestone": "string",\n'
            '      "timeline": "6-12 months",\n'
            '      "success_probability": 0.65\n'
            '    }\n'
            '  ],\n'
            '  "citations": [\n'
            '    {"doi": "doi-string", "idx": 1}\n'
            '  ]\n'
            '}'
        )

        user_msg = (
            f"QUESTION:\n{question}\n\n"
            f"EVIDENCE:\n{evidence_block}{critique_block}\n\n"
            "Respond **ONLY** with valid JSON matching this schema:\n"
            + json_schema
        )

        # ---------------- cost guard-rail: model swap ------------------- #
        prompt_tokens = self._rough_tokens(user_msg)
        max_out_tokens = 1_000  # upper bound for safety
        est_cost = self._estimate_cost(prompt_tokens, max_out_tokens, self.model)

        model_to_use = self.model
        if est_cost > self.cost_threshold and self.model == "gpt-4o":
            model_to_use = "gpt-4o-mini"
            print(
                f"[Lyra] Cost guard-rail: switching to {model_to_use} "
                f"(est. ${est_cost:.3f} > ${self.cost_threshold:.2f})"
            )

        # --------------------------- call ------------------------------- #
        response = self.client.chat.completions.create(
            model=model_to_use,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Lyra, a rigorous scientific-reasoning assistant. "
                        "Your replies **must be JSON only** – no prose."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        # ----------------------- parse & validate ----------------------- #
        try:
            payload: dict = json.loads(response.choices[0].message.content)

            roadmap = [RoadmapItem(**item) for item in payload["roadmap"]]
            citations = [Citation(**c) for c in payload["citations"]]

            return LyraOutput(
                answer=payload["answer"],
                gaps=payload["gaps"],
                roadmap=roadmap,
                citations=citations,
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                "Lyra received non-JSON or malformed JSON:\n"
                + response.choices[0].message.content
            ) from exc
