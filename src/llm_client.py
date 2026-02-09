"""
OpenRouter API client wrapper for Medical Research Prompt Optimizer.

Production-grade LLM client:
- Proper exception handling (no silent failures)
- Structured error messages
- Comprehensive logging
- Type-safe responses
"""
import json
import time
from typing import Dict, Any, Optional

import httpx

from src.telemetry import log_step
from src.config import OPENROUTER_API_KEY, OPENROUTER_URL, HTTP_TIMEOUT
from src.exceptions import LLMCallError, JSONParseError


def call_llm(
    system_prompt: str,
    user_message: str,
    model: str,
    model_params: Optional[Dict[str, Any]] = None,
    response_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call OpenRouter API with system prompt and user message.
    
    Args:
        system_prompt: System prompt text
        user_message: User message text  
        model: Model identifier (e.g., "anthropic/claude-sonnet-4-5")
        model_params: Optional dict of model parameters (temperature, top_k, top_p, etc.)
        response_schema: Optional JSON schema for structured output (future use)
    
    Returns:
        Dict containing:
        - Parsed JSON response from LLM
        - _metadata: Dict with model_used, token_count, latency_ms
    
    Raises:
        LLMCallError: If API call fails (network, auth, rate limit, etc.)
        JSONParseError: If response is not valid JSON
    """
    start_time = time.time()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # Base payload
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000,  # Generous limit for classification/clarification tasks
    }
    
    # Merge in model parameters (temperature, top_k, top_p, etc.)
    if model_params:
        payload.update(model_params)
    
    # Structured output support (tested 2026-02-09 - OpenRouter supports this!)
    # If response_schema provided, use response_format parameter for reliable JSON
    # Spec lines 112-118 document this approach for reliable JSON output
    if response_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "call_response",
                "strict": True,
                "schema": response_schema
            }
        }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/medical-prompt-optimizer",
        "X-Title": "Medical Research Prompt Optimizer",
    }
    
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
    except httpx.HTTPStatusError as e:
        # HTTP error (4xx, 5xx)
        log_step(
            "LLM Call Error",
            details={
                "error_type": "HTTP",
                "status_code": e.response.status_code,
                "model": model,
                "response_preview": e.response.text[:200]
            }
        )
        raise LLMCallError(
            message=f"HTTP {e.response.status_code}",
            model=model,
            status_code=e.response.status_code,
            response_text=e.response.text[:500]
        ) from e
        
    except httpx.TimeoutException as e:
        log_step("LLM Call Error", details={"error_type": "Timeout", "model": model})
        raise LLMCallError(
            message=f"Request timed out after {HTTP_TIMEOUT}s",
            model=model
        ) from e
        
    except Exception as e:
        # Catch-all for network errors, JSON decode errors on response, etc.
        log_step("LLM Call Error", details={"error_type": type(e).__name__, "model": model, "error": str(e)})
        raise LLMCallError(
            message=f"Unexpected error: {str(e)}",
            model=model
        ) from e
    
    # Extract completion text
    if 'choices' not in result or len(result['choices']) == 0:
        log_step("LLM Call Error", details={"error": "No choices in response", "model": model})
        raise LLMCallError(
            message="No choices in API response",
            model=model,
            response_text=json.dumps(result)[:500]
        )
    
    completion_text = result['choices'][0]['message']['content']
    
    # Parse JSON from completion
    try:
        # Try to extract JSON if there's any surrounding text
        json_start = completion_text.find('{')
        json_end = completion_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = completion_text[json_start:json_end]
            parsed = json.loads(json_text)
        else:
            # No braces found, try parsing whole response
            parsed = json.loads(completion_text)
            
    except json.JSONDecodeError as e:
        log_step(
            "JSON Parse Error",
            details={
                "model": model,
                "error": str(e),
                "response_preview": completion_text[:200]
            }
        )
        raise JSONParseError(
            raw_response=completion_text,
            parse_error=str(e)
        ) from e
    
    # Extract token usage and latency
    usage = result.get('usage', {})
    token_count = usage.get('total_tokens', 0)
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Log successful call
    log_step(
        "LLM Call",
        details={
            "model": model,
            "tokens": token_count,
            "latency_ms": latency_ms,
            "success": True
        }
    )
    
    # Add metadata to parsed response
    parsed['_metadata'] = {
        'model_used': model,
        'token_count': token_count,
        'latency_ms': latency_ms,
    }
    
    return parsed
