import json
import os
from openai import OpenAI
from ..app.models import LyraOutput, CriticOutput

class Critic:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def run(self, question: str, lyra_output: LyraOutput) -> CriticOutput:
        """Verify that claims are supported by citations."""
        
        # Format citations for prompt
        citations_text = ""
        for citation in lyra_output.citations:
            citations_text += f"- Citation {citation.idx}: {citation.doi}\n"
        
        prompt = f"""Given the answer and citations, verify each claim is supported.

Question: {question}

Answer: {lyra_output.answer}

Citations:
{citations_text}

Return JSON:
{{
  "passes": true/false,
  "missing_points": ["list of unsupported claims"]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a citation verification agent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return CriticOutput(
            passes=result["passes"],
            missing_points=result["missing_points"]
        ) 