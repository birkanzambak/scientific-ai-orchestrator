#!/usr/bin/env python3
"""Quick setup test to verify the orchestrator works."""

import os
import sys
import json
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from app.models import SophiaOutput, NovaOutput, LyraOutput
        from agents.sophia import Sophia
        from agents.nova import Nova
        from agents.lyra import Lyra
        from agents.critic import Critic
        from services.retriever import search_arxiv
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_models():
    """Test Pydantic models."""
    try:
        from app.models import SophiaOutput, QuestionType
        
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

def test_sophia_mock():
    """Test Sophia with mocked OpenAI."""
    try:
        with patch('openai.OpenAI') as mock_openai:
            client = Mock()
            mock_openai.return_value = client
            
            response = Mock()
            response.choices[0].message.content = '{"question_type": "factual", "keywords": ["test"]}'
            client.chat.completions.create.return_value = response
            
            from agents.sophia import Sophia
            sophia = Sophia()
            result = sophia.run("What is test?")
            
            assert result.question_type.value == "factual"
            assert result.keywords == ["test"]
            print("✓ Sophia agent works with mocks")
            return True
    except Exception as e:
        print(f"✗ Sophia test error: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Scientific AI Orchestrator setup...\n")
    
    tests = [
        test_imports,
        test_models,
        test_sophia_mock,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Setup looks good! You can now run:")
        print("  docker compose up --build")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 