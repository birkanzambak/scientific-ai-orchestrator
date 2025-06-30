#!/usr/bin/env python3
"""Quick test to verify the orchestrator setup works."""

import os
import sys
import json
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_models():
    """Test Pydantic models work."""
    try:
        # Import models directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        from models import SophiaOutput, QuestionType
        
        sophia = SophiaOutput(
            question_type=QuestionType.FACTUAL,
            keywords=["test", "keywords"]
        )
        assert sophia.question_type == QuestionType.FACTUAL
        assert sophia.keywords == ["test", "keywords"]
        print("✓ Pydantic models work")
        return True
    except Exception as e:
        print(f"✗ Model error: {e}")
        return False

def test_openai_import():
    """Test OpenAI import works."""
    try:
        from openai import OpenAI
        print("✓ OpenAI import works")
        return True
    except ImportError as e:
        print(f"✗ OpenAI import error: {e}")
        return False

def test_arxiv_import():
    """Test arXiv import works."""
    try:
        import arxiv
        print("✓ arXiv import works")
        return True
    except ImportError as e:
        print(f"✗ arXiv import error: {e}")
        return False

def test_fastapi_import():
    """Test FastAPI import works."""
    try:
        from fastapi import FastAPI
        print("✓ FastAPI import works")
        return True
    except ImportError as e:
        print(f"✗ FastAPI import error: {e}")
        return False

def test_celery_import():
    """Test Celery import works."""
    try:
        from celery import Celery
        print("✓ Celery import works")
        return True
    except ImportError as e:
        print(f"✗ Celery import error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Quick Scientific AI Orchestrator Test")
    print("=" * 40)
    
    tests = [
        test_models,
        test_openai_import,
        test_arxiv_import,
        test_fastapi_import,
        test_celery_import,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All dependencies are working!")
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY in .env file")
        print("2. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
        print("3. Start API: uvicorn app.main:app --reload")
        print("4. Start worker: celery -A app.workers worker --loglevel=info")
        print("5. Run smoke test: python smoke_test.py")
        return 0
    else:
        print("❌ Some dependencies are missing. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 