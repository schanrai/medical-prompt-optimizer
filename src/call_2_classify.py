"""
Call 2: Classification

Evaluates medical research questions against rule sets to determine if they're
structurally complete and specific enough for meaningful research results.

Production-grade implementation:
- Raises exceptions on failure (no silent None returns)
- Uses centralized config for paths
- Comprehensive error context
"""
from datetime import datetime
from uuid import uuid4
from typing import Optional, List

from src.llm_client import call_llm
from src.schemas import Call2Response, Classification
from src.constants import CALL_2_MODEL, CALL_2_PARAMS, PROMPT_VERSION
from src.telemetry import log_step
from src.config import PROMPTS_DIR
from src.exceptions import LLMCallError, JSONParseError, ValidationError
from src.json_schemas import CALL_2_SCHEMA

# Load system prompt
PROMPT_FILE = PROMPTS_DIR / "call_2_system.txt"
with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()


def run_call_2(user_input: str, question_id: Optional[str] = None) -> Call2Response:
    """
    Run Call 2: Classification against rule sets.
    
    Args:
        user_input: Raw user question (already passed Call 1)
        question_id: Optional UUID (generated if not provided)
    
    Returns:
        Call2Response with classification and triggered rules
        
    Raises:
        LLMCallError: If LLM API call fails
        JSONParseError: If response is invalid JSON
        ValidationError: If response doesn't match expected schema
    """
    if question_id is None:
        question_id = str(uuid4())
    
    log_step("Call 2", question_id=question_id, details={"input_preview": user_input[:50] + "..."})
    
    # Format system prompt with user input
    system_prompt = SYSTEM_PROMPT_TEMPLATE.replace("{user_input}", user_input)
    
    # Send formatted prompt as system message, simple instruction as user message
    response = call_llm(
        system_prompt=system_prompt,
        user_message="Please classify the question above.",
        model=CALL_2_MODEL,
        model_params=CALL_2_PARAMS,
        response_schema=CALL_2_SCHEMA,
    )
    
    # Extract metadata
    metadata = response.pop('_metadata', {})
    model_used = metadata.get('model_used', CALL_2_MODEL)
    token_count = metadata.get('token_count', 0)
    latency_ms = metadata.get('latency_ms', 0)
    
    # Parse classification enum
    classification_str = response.get('classification', '')
    try:
        classification = Classification(classification_str)
    except ValueError as e:
        raise ValidationError(
            f"Invalid classification: {classification_str}. Must be: UNDERSPECIFIED or READY",
            response_data=response
        ) from e
    
    # Get triggered rules
    triggered_rules = response.get('triggered_rules', [])
    
    # Validate rule consistency per spec lines 1094-1097
    if classification == Classification.READY and len(triggered_rules) > 0:
        raise ValidationError(
            f"Classification is READY but triggered_rules is not empty: {triggered_rules}",
            response_data=response
        )
    
    if classification == Classification.UNDERSPECIFIED and len(triggered_rules) == 0:
        raise ValidationError(
            "Classification is UNDERSPECIFIED but triggered_rules is empty",
            response_data=response
        )
    
    # Build and validate response using Pydantic
    try:
        call2_response = Call2Response(
            question_id=question_id,
            call=2,
            classification=classification,
            triggered_rules=triggered_rules,
            reasoning=response.get('reasoning', ''),
            personal_health_referenced=response.get('personal_health_referenced', False),
            model_used=model_used,
            token_count=token_count,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        raise ValidationError(
            f"Failed to construct Call2Response: {str(e)}",
            response_data=response
        ) from e
    
    # Log successful classification
    log_step("Call 2", question_id=question_id, details={
        "classification": classification.value,
        "triggered_rules": triggered_rules,
        "tokens": token_count,
        "latency_ms": latency_ms
    })
    
    return call2_response


if __name__ == "__main__":
    """Standalone test runner for Call 2."""
    from src.exceptions import MPOError
    
    print("=" * 60)
    print("Call 2 Standalone Test")
    print("=" * 60)
    
    # Test cases from corpus
    test_cases = [
        {
            "name": "Clean edge - UNDERSPECIFIED (Q007)",
            "input": "What does the research say about stem cell injections for orthopaedic issues?",
            "expected": "UNDERSPECIFIED (missing_population, missing_scope, undefined_criteria)"
        },
        {
            "name": "Clean edge - UNDERSPECIFIED (Q002)",
            "input": "Explain EDS to me. What should I do if I have strong clinical suspicion I have this?",
            "expected": "UNDERSPECIFIED (multi_intent, missing_population)"
        },
        {
            "name": "Messy edge - UNDERSPECIFIED (Q003)",
            "input": "is 300g of melatonin to much???? i've been taking it for 2 weeks and i'm still so tired should i take more or is this bad for me",
            "expected": "UNDERSPECIFIED (missing_scope, requests_conclusion)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Input: {test_case['input'][:80]}...")
        
        try:
            result = run_call_2(test_case['input'])
            print(f"✅ Success")
            print(f"   Classification: {result.classification.value}")
            print(f"   Triggered rules: {result.triggered_rules}")
            print(f"   Personal health: {result.personal_health_referenced}")
            print(f"   Reasoning: {result.reasoning}")
            print(f"   Tokens: {result.token_count}, Latency: {result.latency_ms}ms")
        except MPOError as e:
            print(f"❌ Failed - {type(e).__name__}: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error - {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
