import json
import os
from openai import OpenAI
from ..app.models import SophiaOutput, QuestionType

class Sophia:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def run(self, question: str) -> SophiaOutput:
        """Classify the question and extract keywords."""
        
        prompt = f"""SYSTEM: You are Sophia, a universal question classifier.

USER: {question}

Assistant: Respond in STRICT JSON:
{{
"question_type": "factual|causal|comparative|mechanism|prediction",
"keywords": ["...", "..."]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are Sophia, a universal question classifier."},
                {"role": "user", "content": question}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return SophiaOutput(
            question_type=QuestionType(result["question_type"]),
            keywords=result["keywords"]
        ) 