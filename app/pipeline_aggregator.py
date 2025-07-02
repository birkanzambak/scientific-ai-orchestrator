"""
Pipeline Aggregator
-------------------

Transforms the outputs from all agents (Sophia, Nova, Lyra, Critic) into a unified
format that matches the test expectations.
"""

from typing import Dict, Any
from app.models import TaskResult


def aggregate_pipeline_output(task_result: TaskResult) -> Dict[str, Any]:
    """
    Transform TaskResult into the test-expected format.
    
    Expected keys: claim, confidence, support_level, rationale, caveats, next_experiment, citations
    """
    if not task_result.lyra_output:
        raise ValueError("No Lyra output available for aggregation")
    
    lyra = task_result.lyra_output
    critic = task_result.critic_output
    
    # Extract claim from Lyra's answer (first sentence or key phrase)
    claim = lyra.answer.split('.')[0] if lyra.answer else "No claim available"
    
    # Confidence based on Critic's assessment
    confidence = 0.8 if critic and critic.passes else 0.5
    
    # Support level from Critic (validated)
    support_level = "weak"  # default
    if critic and hasattr(critic, 'support_level'):
        support_level = critic.support_level
    elif critic and critic.passes:
        support_level = "moderate"
    
    # Rationale is Lyra's answer
    rationale = lyra.answer
    
    # Caveats from Lyra's gaps
    caveats = "; ".join(lyra.gaps) if lyra.gaps else "Limited evidence available"
    
    # Next experiment from roadmap
    next_experiment = ""
    if lyra.roadmap:
        next_experiment = lyra.roadmap[0].next_milestone
    
    # Citations with title and doi
    citations = []
    for citation in lyra.citations:
        citations.append({
            "title": citation.title,
            "doi": citation.doi
        })
    
    return {
        "claim": claim,
        "confidence": confidence,
        "support_level": support_level,
        "rationale": rationale,
        "caveats": caveats,
        "next_experiment": next_experiment,
        "citations": citations,
        # Include nova_output for evidence testing
        "nova_output": {
            "evidence": [
                {"doi": item.doi, "title": item.title, "source": item.source}
                for item in (task_result.nova_output.evidence if task_result.nova_output else [])
            ]
        }
    } 