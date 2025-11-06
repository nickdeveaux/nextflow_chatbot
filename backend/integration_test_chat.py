"""
Simple smoke test for the chat endpoint.
Run with: python test_chat.py
Make sure the backend is running on http://localhost:8000
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_chat():
    """Test the chat endpoint with sample questions."""
    test_cases = [
        "What is the latest version of Nextflow?",
        "Are from and into parts of DSL2 syntax?",
        "Does Nextflow support a Moab executor?",
    ]
    
    session_id = None
    
    for i, question in enumerate(test_cases):
        print(f"\n[{i+1}] Testing: {question}")
        
        payload = {
            "message": question,
            "session_id": session_id
        }
        
        try:
            response = requests.post(f"{API_URL}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ Response: {data['reply'][:100]}...")
            session_id = data.get("session_id")
            print(f"  Session ID: {session_id}")
            
            if data.get("citations"):
                print(f"  Citations: {data['citations']}")
        
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")
            return False
    
    # Test follow-up question
    print("\n[4] Testing follow-up: 'What was that version again?'")
    payload = {
        "message": "What was that version again?",
        "session_id": session_id
    }
    
    try:
        response = requests.post(f"{API_URL}/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Response: {data['reply'][:100]}...")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return False
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✓ Backend is running")
            test_chat()
        else:
            print("✗ Backend health check failed")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend. Make sure it's running on http://localhost:8000")
        print("  Start it with: cd backend && uvicorn main:app --reload")


