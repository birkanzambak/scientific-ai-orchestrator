#!/usr/bin/env python3
"""
Analyze batch run results
-------------------------

Reads runs.json and prints a markdown summary of the results.

Usage:
    python scripts/analyze_runs.py

Input format (runs.json):
[
    {
        "id": "q1",
        "question": "Are we alone in the universe?",
        "status": "completed",
        "sophia_output": {...},
        "nova_output": {...},
        "lyra_output": {...},
        "critic_output": {...},
        "error": null,
        "timestamp": "2024-01-01T12:00:00Z"
    }
]
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def load_results(filepath: str = "runs.json") -> List[Dict[str, Any]]:
    """Load results from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            results = json.load(f)
        return results
    except FileNotFoundError:
        print(f"Error: {filepath} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return []

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze results and return summary statistics."""
    if not results:
        return {}
    
    total = len(results)
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    
    # Analyze critic results
    critic_passes = 0
    critic_fails = 0
    
    for result in results:
        if result.get("status") == "completed" and result.get("critic_output"):
            critic_output = result["critic_output"]
            if isinstance(critic_output, dict) and critic_output.get("passes"):
                critic_passes += 1
            else:
                critic_fails += 1
    
    # Analyze question types
    question_types = {}
    for result in results:
        if result.get("status") == "completed" and result.get("sophia_output"):
            sophia_output = result["sophia_output"]
            if isinstance(sophia_output, dict) and sophia_output.get("question_type"):
                q_type = sophia_output["question_type"]
                question_types[q_type] = question_types.get(q_type, 0) + 1
    
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "critic_passes": critic_passes,
        "critic_fails": critic_fails,
        "question_types": question_types
    }

def print_markdown_summary(results: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Print markdown summary of results."""
    print("# Scientific AI Orchestrator - Batch Run Analysis")
    print()
    
    # Overall statistics
    print("## Overall Statistics")
    print()
    print(f"- **Total Questions**: {stats.get('total', 0)}")
    print(f"- **Completed**: {stats.get('completed', 0)}")
    print(f"- **Failed**: {stats.get('failed', 0)}")
    print(f"- **Success Rate**: {stats.get('completed', 0) / max(stats.get('total', 1), 1) * 100:.1f}%")
    print()
    
    # Critic results
    print("## Critic Verification Results")
    print()
    print(f"- **Passed**: {stats.get('critic_passes', 0)}")
    print(f"- **Failed**: {stats.get('critic_fails', 0)}")
    if stats.get('critic_passes', 0) + stats.get('critic_fails', 0) > 0:
        critic_rate = stats.get('critic_passes', 0) / (stats.get('critic_passes', 0) + stats.get('critic_fails', 0)) * 100
        print(f"- **Pass Rate**: {critic_rate:.1f}%")
    print()
    
    # Question type distribution
    if stats.get('question_types'):
        print("## Question Type Distribution")
        print()
        for q_type, count in stats['question_types'].items():
            print(f"- **{q_type}**: {count}")
        print()
    
    # Detailed results
    print("## Detailed Results")
    print()
    print("| ID | Question | Status | Critic | Error |")
    print("|----|----------|--------|--------|-------|")
    
    for result in results:
        question_id = result.get('id', 'N/A')
        question = result.get('question', 'N/A')[:50] + "..." if len(result.get('question', '')) > 50 else result.get('question', 'N/A')
        status = result.get('status', 'N/A')
        
        # Get critic status
        critic_status = "N/A"
        if result.get('critic_output'):
            critic_output = result['critic_output']
            if isinstance(critic_output, dict):
                critic_status = "✅" if critic_output.get('passes') else "❌"
        
        error = result.get('error', '') or ''
        error_display = error[:30] + "..." if len(error) > 30 else error
        
        print(f"| {question_id} | {question} | {status} | {critic_status} | {error_display} |")

def main():
    """Main function to analyze batch run results."""
    print("Scientific AI Orchestrator - Results Analysis")
    print("=" * 50)
    
    # Load results
    results = load_results()
    if not results:
        print("No results found. Please run the batch script first.")
        return
    
    print(f"Loaded {len(results)} results")
    
    # Analyze results
    stats = analyze_results(results)
    
    # Print summary
    print_markdown_summary(results, stats)

if __name__ == "__main__":
    main() 