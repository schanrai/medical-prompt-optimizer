"""
Call 3: Clarification Generator

Generates 2-4 rewrite options that address specific structural issues identified by Call 2.

Production-grade implementation:
- Raises exceptions on failure (no silent None returns)
- Uses centralized config for paths
- Comprehensive error context
"""
from datetime import datetime
from uuid import uuid4
from typing import Optional, List

from src.llm_client import call_llm
from src.schemas import Call3Response, ClarificationOption
from src.constants import CALL_3_MODEL, CALL_3_PARAMS, PROMPT_VERSION
from src.telemetry import log_step
from src.config import PROMPTS_DIR
from src.exceptions import LLMCallError, JSONParseError, ValidationError
from src.json_schemas import CALL_3_SCHEMA

# Load system prompt
PROMPT_FILE = PROMPTS_DIR / "call_3_system.txt"
with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()


def run_call_3(
    user_input: str,
    triggered_rules: List[str],
    reasoning: str,
    question_id: Optional[str] = None
) -> Call3Response:
    """
    Run Call 3: Clarification Generator.
    
    Args:
        user_input: Raw user question (already passed Call 1 and Call 2)
        triggered_rules: List of rule IDs from Call 2 (e.g., ["missing_population", "requests_conclusion"])
        reasoning: Explanation from Call 2 of why those rules triggered
        question_id: Optional UUID (generated if not provided)
    
    Returns:
        Call3Response with 2-4 clarification options
        
    Raises:
        LLMCallError: If LLM API call fails
        JSONParseError: If response is invalid JSON
        ValidationError: If response doesn't match expected schema
    """
    if question_id is None:
        question_id = str(uuid4())
    
    log_step("Call 3", question_id=question_id, details={
        "input_preview": user_input[:50] + "...",
        "triggered_rules": triggered_rules
    })
    
    # Format system prompt with inputs
    # Convert triggered_rules list to JSON array string for prompt
    triggered_rules_str = str(triggered_rules)
    
    system_prompt = SYSTEM_PROMPT_TEMPLATE.replace("{user_input}", user_input)
    system_prompt = system_prompt.replace("{triggered_rules}", triggered_rules_str)
    system_prompt = system_prompt.replace("{reasoning}", reasoning)
    
    # Send formatted prompt as system message, simple instruction as user message
    response = call_llm(
        system_prompt=system_prompt,
        user_message="Please generate clarification options for the question above.",
        model=CALL_3_MODEL,
        model_params=CALL_3_PARAMS,
        response_schema=CALL_3_SCHEMA,
    )
    
    # Extract metadata
    metadata = response.pop('_metadata', {})
    model_used = metadata.get('model_used', CALL_3_MODEL)
    token_count = metadata.get('token_count', 0)
    latency_ms = metadata.get('latency_ms', 0)
    
    # Extract clarification_options
    clarification_options_raw = response.get('clarification_options', [])
    
    # Validate minimum/maximum options count (2-4 required)
    if not isinstance(clarification_options_raw, list):
        raise ValidationError(
            f"clarification_options must be a list, got {type(clarification_options_raw)}",
            response_data=response
        )
    
    if len(clarification_options_raw) < 2:
        raise ValidationError(
            f"clarification_options must contain at least 2 items, got {len(clarification_options_raw)}",
            response_data=response
        )
    
    if len(clarification_options_raw) > 4:
        raise ValidationError(
            f"clarification_options must contain at most 4 items, got {len(clarification_options_raw)}",
            response_data=response
        )
    
    # Parse clarification options into Pydantic models
    try:
        clarification_options = [
            ClarificationOption(**option)
            for option in clarification_options_raw
        ]
    except Exception as e:
        raise ValidationError(
            f"Failed to parse clarification_options: {str(e)}",
            response_data=response
        ) from e
    
    # Build and validate response using Pydantic
    try:
        call3_response = Call3Response(
            question_id=question_id,
            call=3,
            clarification_options=clarification_options,
            reasoning=response.get('reasoning', ''),
            model_used=model_used,
            token_count=token_count,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        raise ValidationError(
            f"Failed to construct Call3Response: {str(e)}",
            response_data=response
        ) from e
    
    # Log successful clarification generation
    log_step("Call 3", question_id=question_id, details={
        "options_generated": len(clarification_options),
        "tokens": token_count,
        "latency_ms": latency_ms
    })
    
    return call3_response


if __name__ == "__main__":
    """Standalone test runner for Call 3."""
    from src.exceptions import MPOError
    
    print("=" * 60)
    print("Call 3 Standalone Test")
    print("=" * 60)
    
    # Test cases from corpus
    test_cases = [
        {
            "name": "Q007 - Stem cell injections (UNDERSPECIFIED)",
            "input": "What does the research say about stem cell injections for orthopaedic issues?",
            "triggered_rules": ["missing_population", "missing_scope", "undefined_criteria"],
            "reasoning": "The question lacks population context (age, activity level), scope constraints (specific orthopaedic condition, injection protocol), and doesn't specify what outcome measure is being evaluated (pain reduction, healing time, functional improvement)."
        },
        {
            "name": "Q002 - EDS multi-intent (UNDERSPECIFIED)",
            "input": "Explain EDS to me. What should I do if I have strong clinical suspicion I have this?",
            "triggered_rules": ["multi_intent", "missing_population"],
            "reasoning": "The question contains two distinct intents (explanation + action recommendation) and lacks population context for the clinical suspicion (age, symptoms, previous testing)."
        },
        {
            "name": "Q003 - Melatonin messy question (UNDERSPECIFIED)",
            "input": "is 300g of melatonin to much???? i've been taking it for 2 weeks and i'm still so tired should i take more or is this bad for me",
            "triggered_rules": ["missing_scope", "requests_conclusion"],
            "reasoning": "The question lacks scope constraints (likely unit error: 300g vs 300mcg), doesn't specify what 'tired' means (sleep quality, daytime energy), and requests a conclusion ('is this bad') rather than evidence."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Input: {test_case['input'][:80]}...")
        print(f"Triggered rules: {test_case['triggered_rules']}")
        
        try:
            result = run_call_3(
                user_input=test_case['input'],
                triggered_rules=test_case['triggered_rules'],
                reasoning=test_case['reasoning']
            )
            print(f"✅ Success")
            print(f"   Options generated: {len(result.clarification_options)}")
            for j, option in enumerate(result.clarification_options, 1):
                print(f"   {j}. [{option.label}] {option.rewritten_question}")
            print(f"   Reasoning: {result.reasoning}")
            print(f"   Tokens: {result.token_count}, Latency: {result.latency_ms}ms")
        except MPOError as e:
            print(f"❌ Failed - {type(e).__name__}: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error - {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
