#!/usr/bin/env python3
"""
Batch processing script for Scientific AI Orchestrator
-------------------------------------------------------

Reads questions from questions.json and runs them through the pipeline,
saving results to runs.json.

Usage:
    python scripts/run_batch.py

Input format (questions.json):
[
    {
        "id": "q1",
        "question": "Are we alone in the universe?",
        "topic_filter": ["astronomy", "biology"]
    },
    {
        "id": "q2", 
        "question": "What is quantum computing?",
        "topic_filter": ["physics", "computer science"]
    }
]

Output format (runs.json):
[
    {
        "id": "q1",
        "question": "Are we alone in the universe?",
        "topic_filter": ["astronomy", "biology"],
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
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.sophia import Sophia
from agents.nova import Nova
from agents.lyra import Lyra
from agents.critic import Critic
from app.models import TaskResult


def load_questions(filepath: str = "questions.json") -> List[Dict[str, Any]]:
    """
    Load questions from JSON file.
    
    Args:
        filepath: Path to questions.json file
        
    Returns:
        List of question dictionaries
        
    Example:
        >>> questions = load_questions("questions.json")
        >>> len(questions) > 0
        True
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        # Validate format
        for q in questions:
            if not isinstance(q, dict):
                raise ValueError("Each question must be a dictionary")
            if "id" not in q or "question" not in q:
                raise ValueError("Each question must have 'id' and 'question' fields")
        
        return questions
    except FileNotFoundError:
        print(f"Error: {filepath} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return []


def save_results(results: List[Dict[str, Any]], filepath: str = "runs.json"):
    """
    Save results to JSON file.
    
    Args:
        results: List of result dictionaries
        filepath: Path to output file
        
    Example:
        >>> results = [{"id": "q1", "status": "completed"}]
        >>> save_results(results, "runs.json")
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Results saved to {filepath}")
    except Exception as e:
        print(f"Error saving results: {e}")


def run_single_question(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single question through the pipeline.
    
    Args:
        question_data: Question dictionary with id, question, and optional topic_filter
        
    Returns:
        Result dictionary with all outputs and metadata
        
    Example:
        >>> question = {"id": "q1", "question": "What is AI?"}
        >>> result = run_single_question(question)
        >>> result["status"] in ["completed", "failed"]
        True
    """
    question_id = question_data["id"]
    question_text = question_data["question"]
    topic_filter = question_data.get("topic_filter")
    
    print(f"\n--- Processing Question {question_id} ---")
    print(f"Question: {question_text}")
    if topic_filter:
        print(f"Topic filter: {topic_filter}")
    
    result = {
        "id": question_id,
        "question": question_text,
        "topic_filter": topic_filter,
        "status": "running",
        "sophia_output": None,
        "nova_output": None,
        "lyra_output": None,
        "critic_output": None,
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        # Step 1: Sophia
        print("  Running Sophia...")
        sophia = Sophia()
        sophia_output = sophia.run(question_text)
        result["sophia_output"] = sophia_output.__dict__
        print(f"  ✓ Sophia: {sophia_output.question_type} - {sophia_output.keywords}")
        
        # Step 2: Nova
        print("  Running Nova...")
        nova = Nova()
        nova_output = nova.run(sophia_output)
        result["nova_output"] = nova_output.__dict__
        print(f"  ✓ Nova: Found {len(nova_output.evidence)} evidence items")
        
        # Step 3: Lyra
        print("  Running Lyra...")
        lyra = Lyra()
        lyra_output = lyra.run(question_text, nova_output)
        result["lyra_output"] = lyra_output.__dict__
        print(f"  ✓ Lyra: Hypothesis probability {lyra_output.hypothesis_probability:.2f}")
        
        # Step 4: Critic
        print("  Running Critic...")
        critic = Critic()
        critic_output = critic.run(question_text, lyra_output)
        result["critic_output"] = critic_output.__dict__
        print(f"  ✓ Critic: {'PASS' if critic_output.passes else 'FAIL'}")
        
        # Step 5: Optional rerun if critic fails
        if not critic_output.passes:
            print("  Critic failed, running Lyra rerun...")
            lyra_output = lyra.run(question_text, nova_output, 
                                 critique={"missing_points": critic_output.missing_points})
            result["lyra_output"] = lyra_output.__dict__
            
            print("  Running Critic again...")
            critic_output = critic.run(question_text, lyra_output)
            result["critic_output"] = critic_output.__dict__
            print(f"  ✓ Critic (rerun): {'PASS' if critic_output.passes else 'FAIL'}")
        
        result["status"] = "completed"
        print(f"  ✓ Question {question_id} completed successfully")
        
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        print(f"  ✗ Question {question_id} failed: {e}")
    
    return result


def main():
    """Main function to run batch processing."""
    print("Scientific AI Orchestrator - Batch Processing")
    print("=" * 50)
    
    # Load questions
    questions = load_questions()
    if not questions:
        print("No questions found. Please create a questions.json file.")
        return
    
    print(f"Loaded {len(questions)} questions")
    
    # Process each question
    results = []
    start_time = time.time()
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Processing question {question['id']}...")
        
        result = run_single_question(question)
        results.append(result)
        
        # Save intermediate results
        if i % 5 == 0 or i == len(questions):
            save_results(results, "runs_intermediate.json")
            print(f"  Intermediate results saved ({i}/{len(questions)} completed)")
    
    # Save final results
    save_results(results, "runs.json")
    
    # Print summary
    elapsed_time = time.time() - start_time
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    
    print(f"\n" + "=" * 50)
    print("BATCH PROCESSING COMPLETE")
    print(f"Total questions: {len(questions)}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Total time: {elapsed_time:.1f} seconds")
    print(f"Average time per question: {elapsed_time/len(questions):.1f} seconds")
    
    if failed > 0:
        print(f"\nFailed questions:")
        for result in results:
            if result["status"] == "failed":
                print(f"  - {result['id']}: {result['error']}")


if __name__ == "__main__":
    main() 