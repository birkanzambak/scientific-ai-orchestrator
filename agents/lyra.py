import json
import os
from openai import OpenAI
from ..app.models import NovaOutput, LyraOutput, RoadmapItem, Citation

class Lyra:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.cost_threshold = float(os.getenv("COST_THRESHOLD", "0.05"))  # USD
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token)."""
        return len(text) // 4
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost in USD."""
        # OpenAI pricing (approximate, as of 2024)
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}  # per 1K tokens
        }
        
        if model not in pricing:
            model = "gpt-4o-mini"  # fallback
        
        cost = (input_tokens / 1000) * pricing[model]["input"] + (output_tokens / 1000) * pricing[model]["output"]
        return cost
    
    def run(self, question: str, nova_output: NovaOutput, critique: dict = None) -> LyraOutput:
        """Reason over evidence and generate answer with research roadmap."""
        
        # Format evidence for prompt
        evidence_text = ""
        for i, item in enumerate(nova_output.evidence, 1):
            evidence_text += f"{i}. {item.title}\n"
            evidence_text += f"   DOI: {item.doi}\n"
            evidence_text += f"   Summary: {item.summary}\n\n"
        
        critique_text = ""
        if critique:
            critique_text = f"\nPrevious critique identified issues: {critique.get('missing_points', [])}"
        
        prompt = f"""You are Lyra, a scientific reasoning agent. Analyze the evidence and answer the question.

Question: {question}

Evidence:
{evidence_text}{critique_text}

Respond in STRICT JSON:
{{
  "answer": "comprehensive answer based on evidence",
  "gaps": ["list of knowledge gaps"],
  "roadmap": [
    {{
      "priority": 1,
      "research_area": "specific area",
      "next_milestone": "concrete milestone",
      "timeline": "6-12 months",
      "success_probability": 0.65
    }}
  ],
  "citations": [
    {{ "doi": "paper_doi", "idx": 1 }}
  ]
}}"""

        # Estimate tokens and cost
        input_tokens = self.estimate_tokens(prompt)
        estimated_output_tokens = 1000  # conservative estimate
        estimated_cost = self.estimate_cost(input_tokens, estimated_output_tokens, self.model)
        
        # Downgrade model if cost exceeds threshold
        model_to_use = self.model
        if estimated_cost > self.cost_threshold and self.model == "gpt-4o":
            model_to_use = "gpt-4o-mini"
            print(f"Cost guard-rail: Downgrading from {self.model} to {model_to_use} (estimated cost: ${estimated_cost:.4f})")

        response = self.client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": "You are Lyra, a scientific reasoning agent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Convert roadmap items
        roadmap = [
            RoadmapItem(**item) for item in result["roadmap"]
        ]
        
        # Convert citations
        citations = [
            Citation(**citation) for citation in result["citations"]
        ]
        
        return LyraOutput(
            answer=result["answer"],
            gaps=result["gaps"],
            roadmap=roadmap,
            citations=citations
        ) 