#!/usr/bin/env python3
"""Local smoke test for the Scientific AI Orchestrator."""

import os
import sys
import time
import json
import requests
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_health_endpoint():
    """Test the health endpoint."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint working")
            return True
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Health endpoint error: {e}")
        return False

def test_ask_endpoint():
    """Test the ask endpoint."""
    try:
        payload = {"question": "Why do stars explode?"}
        response = requests.post(
            "http://localhost:8000/ask",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✓ Ask endpoint working, got task_id: {task_id}")
            return task_id
        else:
            print(f"✗ Ask endpoint failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Ask endpoint error: {e}")
        return None

def test_result_endpoint(task_id):
    """Test the result endpoint."""
    if not task_id:
        return False
    
    max_attempts = 15  # 30 seconds total
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://localhost:8000/result/{task_id}", timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                print(f"✓ Result endpoint working, status: {status}")
                
                if status == "completed":
                    # Check for expected fields
                    if result.get("lyra_output") and result.get("lyra_output", {}).get("answer"):
                        print("✓ Full pipeline completed successfully!")
                        print(f"  Answer: {result['lyra_output']['answer'][:100]}...")
                        return True
                    else:
                        print("✗ Pipeline completed but missing expected data")
                        return False
                elif status == "failed":
                    error = result.get("error", "Unknown error")
                    print(f"✗ Pipeline failed: {error}")
                    return False
                else:
                    print(f"  Still processing... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(2)
            else:
                print(f"✗ Result endpoint failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Result endpoint error: {e}")
            return False
    
    print("✗ Pipeline timed out")
    return False

def test_stream_endpoint(task_id):
    """Test the SSE stream endpoint."""
    if not task_id:
        return False
    
    try:
        response = requests.get(f"http://localhost:8000/stream/{task_id}", timeout=5)
        if response.status_code == 200:
            print("✓ Stream endpoint working")
            return True
        else:
            print(f"✗ Stream endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Stream endpoint error: {e}")
        return False

def test_openapi_docs():
    """Test the OpenAPI docs endpoint."""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✓ OpenAPI docs working")
            return True
        else:
            print(f"✗ OpenAPI docs failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ OpenAPI docs error: {e}")
        return False

def main():
    """Run the smoke test."""
    print("🔥 Scientific AI Orchestrator Smoke Test")
    print("=" * 50)
    
    # Check if API is running
    print("\n1. Testing API endpoints...")
    if not test_health_endpoint():
        print("\n❌ API is not running. Start it with:")
        print("   uvicorn app.main:app --reload")
        return 1
    
    if not test_openapi_docs():
        print("❌ OpenAPI docs not accessible")
        return 1
    
    # Test ask endpoint
    print("\n2. Testing question submission...")
    task_id = test_ask_endpoint()
    if not task_id:
        print("❌ Could not submit question")
        return 1
    
    # Test stream endpoint
    print("\n3. Testing stream endpoint...")
    if not test_stream_endpoint(task_id):
        print("❌ Stream endpoint not working")
        return 1
    
    # Test result endpoint and wait for completion
    print("\n4. Testing pipeline execution...")
    if not test_result_endpoint(task_id):
        print("❌ Pipeline execution failed")
        return 1
    
    print("\n🎉 All smoke tests passed!")
    print("\nNext steps:")
    print("1. Deploy to production (Render/Railway)")
    print("2. Connect frontend")
    print("3. Invite beta users")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 