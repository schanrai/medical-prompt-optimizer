#!/usr/bin/env python3
"""
Test script for OpenRouter API connection
"""
import os
import json
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def test_openrouter_connection():
    """Test basic OpenRouter API connection with a simple completion"""

    api_key = os.getenv('OPENROUTER_API_KEY')

    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in .env file")
        return False

    print("✓ API key loaded from .env")
    print(f"✓ Key starts with: {api_key[:10]}...")

    # OpenRouter API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"

    # Request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Simple test prompt
    data = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from OpenRouter!' in exactly 5 words."
            }
        ],
        "max_tokens": 50
    }

    print("\n🔄 Testing OpenRouter API connection...")
    print(f"   Model: {data['model']}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Extract the completion
        if 'choices' in result and len(result['choices']) > 0:
            completion = result['choices'][0]['message']['content']
            print("\n✅ SUCCESS! OpenRouter API is working.")
            print(f"\n📝 Response from API:")
            print(f"   {completion}")

            # Show token usage if available
            if 'usage' in result:
                usage = result['usage']
                print(f"\n📊 Token Usage:")
                print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")

            return True
        else:
            print("❌ ERROR: Unexpected response format")
            print(json.dumps(result, indent=2))
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: Request failed")
        print(f"   {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"\n   Response status: {e.response.status_code}")
            try:
                print(f"   Response body: {e.response.json()}")
            except:
                print(f"   Response body: {e.response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenRouter API Connection Test")
    print("=" * 60)

    success = test_openrouter_connection()

    print("\n" + "=" * 60)
    if success:
        print("✅ Test PASSED - Ready to proceed")
    else:
        print("❌ Test FAILED - Check errors above")
    print("=" * 60)
