"""
Telemetry logging for Medical Research Prompt Optimizer.

Provides two outputs:
1. Structured console logging (colored, readable for development)
2. Append-only JSONL file logging (logs/telemetry.jsonl)

All pipeline stages write to both outputs immediately.
"""
import json
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

from src.config import TELEMETRY_FILE

# Configure console logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def normalize_input(text: str) -> str:
    """Normalize input for hashing (lowercase, whitespace collapsed)."""
    return " ".join(text.lower().split())


def compute_input_hash(raw_input: str) -> str:
    """Compute SHA-256 hash of normalized input for brittleness detection."""
    normalized = normalize_input(raw_input)
    return hashlib.sha256(normalized.encode()).hexdigest()


def log_step(
    step_name: str,
    question_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a single pipeline step for development debugging.
    
    Used during development to see what each stage is doing.
    Example: log_step("Call 1", question_id="abc123", details={"is_medical": True})
    """
    msg_parts = [f"[{step_name}]"]
    if question_id:
        msg_parts.append(f"question_id={question_id[:8]}...")
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg_parts.append(detail_str)
    
    logger.info(" ".join(msg_parts))


def log_run(entry: Dict[str, Any]) -> None:
    """
    Log a complete pipeline run to both console and JSONL file.
    
    Entry should contain all fields from spec lines 1062-1074:
    - question_id (UUID string)
    - raw_input (original question verbatim)
    - input_hash (SHA-256 of normalized input)
    - classification_result (OUT_OF_SCOPE | UNDERSPECIFIED | READY)
    - routing_decision (security_violation | non_medical | non_english | clarification | confirmation)
    - triggered_rules (array of rule IDs)
    - prompt_version (e.g., "v1.0")
    - model_version (exact model version string)
    - token_count (total tokens)
    - latency_ms (end-to-end processing time)
    - timestamp (ISO8601)
    - outcome (clarification_options | confirmed_prompt | out_of_scope_redirect)
    """
    # Ensure timestamp is present
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # Console output (readable summary)
    logger.info(f"Pipeline run complete: {entry.get('classification_result', 'UNKNOWN')} "
                f"(routing: {entry.get('routing_decision', 'UNKNOWN')}, "
                f"latency: {entry.get('latency_ms', 0)}ms, "
                f"tokens: {entry.get('token_count', 0)})")
    
    # JSONL file output (append-only); skip if read-only filesystem (e.g. Vercel)
    try:
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # logs/ not writable; console output above is sufficient
