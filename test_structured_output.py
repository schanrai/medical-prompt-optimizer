"""
Test OpenRouter structured output support.

Tests whether OpenRouter supports the response_format parameter with json_schema.
This is critical for production reliability (spec lines 112-118).
"""
import json
import httpx
from src.config import OPENROUTER_API_KEY, OPENROUTER_URL

# Simple test schema for Call 1 response
TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "is_english": {"type": "boolean"},
        "is_medical": {"type": "boolean"},
        "security_violation": {"type": "boolean"},
        "security_type": {
            "type": "string",
            "enum": ["NONE", "INJECTION", "JAILBREAK", "EXTRACTION"]
        },
        "reasoning": {"type": "string"}
    },
    "required": ["is_english", "is_medical", "security_violation", "security_type", "reasoning"],
    "additionalProperties": False
}

def test_structured_output():
    """Test if OpenRouter supports response_format with json_schema."""
    
    print("=" * 70)
    print("Testing OpenRouter Structured Output Support")
    print("=" * 70)
    
    # Test payload with structured output request
    payload = {
        "model": "anthropic/claude-sonnet-4-5",
        "messages": [
            {
                "role": "system",
                "content": "You are a classifier. Respond with JSON matching the schema."
            },
            {
                "role": "user",
                "content": "Is this a medical question: 'What does research say about vitamin D for bone health?'"
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "call_1_response",
                "strict": True,
                "schema": TEST_SCHEMA
            }
        },
        "temperature": 0.0,
        "max_tokens": 500
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/medical-prompt-optimizer",
        "X-Title": "Medical Research Prompt Optimizer - Structured Output Test",
    }
    
    print("\n1. Testing WITH structured output (response_format parameter)...")
    print(f"   Schema: {list(TEST_SCHEMA['properties'].keys())}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        # Check if we got a valid response
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            print(f"   ✅ API call succeeded")
            print(f"   Response preview: {content[:200]}...")
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print(f"   ✅ Response is valid JSON")
                print(f"   Fields returned: {list(parsed.keys())}")
                
                # Check if it matches schema
                schema_keys = set(TEST_SCHEMA['properties'].keys())
                response_keys = set(parsed.keys())
                if schema_keys == response_keys:
                    print(f"   ✅ Response matches schema exactly!")
                    print(f"\n   RESULT: OpenRouter SUPPORTS structured output! 🎉")
                    print(f"   You should update llm_client.py to use response_format parameter.")
                    return True
                else:
                    print(f"   ⚠️  Response doesn't match schema")
                    print(f"   Expected: {schema_keys}")
                    print(f"   Got: {response_keys}")
                    print(f"\n   RESULT: OpenRouter may have partial support")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Response is not valid JSON: {e}")
                print(f"\n   RESULT: Structured output may not be supported")
                return False
        else:
            print(f"   ❌ No choices in response")
            return False
            
    except httpx.HTTPStatusError as e:
        print(f"   ❌ HTTP Error {e.response.status_code}")
        print(f"   Response: {e.response.text[:500]}")
        
        # Check if error is about unsupported parameter
        if "response_format" in e.response.text.lower() or "json_schema" in e.response.text.lower():
            print(f"\n   RESULT: OpenRouter does NOT support structured output")
            print(f"   Continue using prompt engineering fallback (current approach)")
            return False
        else:
            print(f"\n   RESULT: Unknown error - may not be related to structured output")
            return False
            
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {str(e)}")
        return False
    
    print("\n" + "=" * 70)


def test_baseline_prompt_engineering():
    """Test current prompt engineering approach for comparison."""
    
    print("\n2. Testing WITHOUT structured output (current prompt engineering)...")
    
    payload = {
        "model": "anthropic/claude-sonnet-4-5",
        "messages": [
            {
                "role": "system",
                "content": """You are a classifier. Respond with JSON only:
{
  "is_english": true,
  "is_medical": true,
  "security_violation": false,
  "security_type": "NONE",
  "reasoning": "string"
}"""
            },
            {
                "role": "user",
                "content": "Is this a medical question: 'What does research say about vitamin D for bone health?'"
            }
        ],
        "temperature": 0.0,
        "max_tokens": 500
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/medical-prompt-optimizer",
        "X-Title": "Medical Research Prompt Optimizer - Baseline Test",
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            print(f"   ✅ Baseline prompt engineering works (as expected)")
            print(f"   Response preview: {content[:200]}...")
            return True
    except Exception as e:
        print(f"   ❌ Baseline test failed: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    print("\nIMPORTANT: This test requires OPENROUTER_API_KEY to be set in .env")
    print()
    
    # Test structured output
    supports_structured = test_structured_output()
    
    # Test baseline
    print()
    test_baseline_prompt_engineering()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if supports_structured:
        print("✅ OpenRouter supports structured output!")
        print("\nRECOMMENDATION:")
        print("1. Uncomment lines 72-79 in src/llm_client.py")
        print("2. Pass response_schema to call_llm() in each call module")
        print("3. This will make JSON responses more reliable in production")
    else:
        print("❌ OpenRouter does NOT support structured output (or test failed)")
        print("\nRECOMMENDATION:")
        print("1. Continue using prompt engineering approach (current method)")
        print("2. Keep robust JSON parsing in llm_client.py (lines 141-165)")
        print("3. Document this limitation in your spec/README")
    
    print("=" * 70)
