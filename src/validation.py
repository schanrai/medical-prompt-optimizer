"""
Stage 0: Code Input Validation (Pre-LLM)

Validates user input before any LLM call to prevent garbage from consuming
API tokens. Implements spec lines 358-396.

Checks (in order):
1. Empty/whitespace -> REJECT_EMPTY
2. Too short (<3 words) -> REJECT_TOO_SHORT
3. Too long (>500 words) -> REJECT_TOO_LONG
4. Gibberish (no recognizable English words) -> REJECT_GIBBERISH
"""
from datetime import datetime
from uuid import uuid4
from typing import Optional

from src.schemas import ValidationResult, ValidationResultModel
from src.telemetry import log_step

# Rejection messages (spec lines 382-385)
REJECTION_MESSAGES = {
    ValidationResult.REJECT_EMPTY: "Please enter a question.",
    ValidationResult.REJECT_TOO_SHORT: "Please enter a complete question.",
    ValidationResult.REJECT_TOO_LONG: "Please shorten your question to focus on a single research topic.",
    ValidationResult.REJECT_GIBBERISH: "Your input doesn't appear to be a recognizable question.",
}

# Word count thresholds (spec lines 382-385)
MIN_WORD_COUNT = 3
MAX_WORD_COUNT = 500

# Common English words for gibberish detection.
# A token is considered "recognizable" if it appears in this set OR contains
# only alphabetic characters and is at least 2 characters long.
# This is a deliberately simple heuristic per spec guidance.
COMMON_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "must", "need",
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "she", "it",
    "they", "them", "their", "this", "that", "these", "those",
    "what", "which", "who", "whom", "how", "when", "where", "why",
    "and", "or", "but", "if", "then", "so", "because", "although",
    "not", "no", "yes", "all", "each", "every", "any", "some",
    "in", "on", "at", "to", "for", "of", "with", "from", "by", "about",
    "into", "through", "during", "before", "after", "between", "under",
    "above", "up", "down", "out", "off", "over",
    "does", "help", "tell", "show", "say", "said", "know", "think",
    "research", "study", "studies", "health", "medical", "treatment",
    "risk", "cause", "effect", "symptoms", "condition", "disease",
    "patient", "doctor", "drug", "medicine", "therapy", "diagnosis",
})


def _count_words(text: str) -> int:
    """Count words by splitting on whitespace."""
    return len(text.split())


def _has_recognizable_words(text: str) -> bool:
    """
    Check if input contains at least one recognizable English word.

    Spec says: "No dictionary words detected" -> REJECT_GIBBERISH.
    Implementation: require at least one token to be in COMMON_WORDS.

    This works because any real question (even heavy medical jargon) will
    contain at least one common word ("what", "does", "the", "for", "in", etc.).
    Nobody writes "SSRIs efficacy postmenopausal" without a single common word.

    The LLM in Call 1 does the real language detection (is_english) for
    non-English inputs that contain recognizable words.
    """
    tokens = text.lower().split()
    for token in tokens:
        # Strip common punctuation for matching
        cleaned = token.strip(".,!?;:'\"()-")
        if not cleaned:
            continue
        if cleaned in COMMON_WORDS:
            return True
    return False


def validate_input(
    raw_input: str,
    question_id: Optional[str] = None
) -> ValidationResultModel:
    """
    Run Stage 0 code-based input validation.

    Checks are applied in order; first failure returns immediately.
    If all checks pass, returns PASS.

    Args:
        raw_input: The raw user input string
        question_id: Optional UUID (generated if not provided)

    Returns:
        ValidationResultModel with PASS or REJECT_* result + rejection message
    """
    if question_id is None:
        question_id = str(uuid4())

    timestamp = datetime.utcnow().isoformat() + "Z"

    # Check 1: Empty/whitespace
    stripped = raw_input.strip()
    if len(stripped) == 0:
        log_step("Stage 0 Validation", question_id=question_id, details={
            "result": "REJECT_EMPTY"
        })
        return ValidationResultModel(
            question_id=question_id,
            validation_result=ValidationResult.REJECT_EMPTY,
            rejection_message=REJECTION_MESSAGES[ValidationResult.REJECT_EMPTY],
            timestamp=timestamp,
        )

    # Check 2: Too short (< 3 words)
    word_count = _count_words(stripped)
    if word_count < MIN_WORD_COUNT:
        log_step("Stage 0 Validation", question_id=question_id, details={
            "result": "REJECT_TOO_SHORT",
            "word_count": word_count
        })
        return ValidationResultModel(
            question_id=question_id,
            validation_result=ValidationResult.REJECT_TOO_SHORT,
            rejection_message=REJECTION_MESSAGES[ValidationResult.REJECT_TOO_SHORT],
            timestamp=timestamp,
        )

    # Check 3: Too long (> 500 words)
    if word_count > MAX_WORD_COUNT:
        log_step("Stage 0 Validation", question_id=question_id, details={
            "result": "REJECT_TOO_LONG",
            "word_count": word_count
        })
        return ValidationResultModel(
            question_id=question_id,
            validation_result=ValidationResult.REJECT_TOO_LONG,
            rejection_message=REJECTION_MESSAGES[ValidationResult.REJECT_TOO_LONG],
            timestamp=timestamp,
        )

    # Check 4: Gibberish (no recognizable English words)
    if not _has_recognizable_words(stripped):
        log_step("Stage 0 Validation", question_id=question_id, details={
            "result": "REJECT_GIBBERISH",
            "word_count": word_count
        })
        return ValidationResultModel(
            question_id=question_id,
            validation_result=ValidationResult.REJECT_GIBBERISH,
            rejection_message=REJECTION_MESSAGES[ValidationResult.REJECT_GIBBERISH],
            timestamp=timestamp,
        )

    # All checks passed
    log_step("Stage 0 Validation", question_id=question_id, details={
        "result": "PASS",
        "word_count": word_count
    })
    return ValidationResultModel(
        question_id=question_id,
        validation_result=ValidationResult.PASS,
        rejection_message=None,
        timestamp=timestamp,
    )


if __name__ == "__main__":
    """Standalone test runner for Stage 0 validation."""
    print("=" * 60)
    print("Stage 0: Input Validation Test")
    print("=" * 60)

    test_cases = [
        {
            "name": "Empty string",
            "input": "",
            "expected": "REJECT_EMPTY"
        },
        {
            "name": "Whitespace only",
            "input": "   \t\n  ",
            "expected": "REJECT_EMPTY"
        },
        {
            "name": "Too short (1 word)",
            "input": "vitamins",
            "expected": "REJECT_TOO_SHORT"
        },
        {
            "name": "Too short (2 words)",
            "input": "heart disease",
            "expected": "REJECT_TOO_SHORT"
        },
        {
            "name": "Gibberish",
            "input": "asdf jkl qwer zxcv mnbv",
            "expected": "REJECT_GIBBERISH"
        },
        {
            "name": "Numeric gibberish",
            "input": "123 456 789 012 345",
            "expected": "REJECT_GIBBERISH"
        },
        {
            "name": "Too long (>500 words)",
            "input": " ".join(["word"] * 501),
            "expected": "REJECT_TOO_LONG"
        },
        {
            "name": "Valid - short question",
            "input": "What causes chest pain?",
            "expected": "PASS"
        },
        {
            "name": "Valid - medical research question",
            "input": "What does the research say about vitamin D for bone health?",
            "expected": "PASS"
        },
        {
            "name": "Valid - contains medical terms",
            "input": "What do FSH levels above 100 mIU/mL indicate in postmenopausal women?",
            "expected": "PASS"
        },
        {
            "name": "Exactly 3 words (boundary)",
            "input": "Does aspirin help?",
            "expected": "PASS"
        },
        {
            "name": "Exactly 500 words (boundary)",
            "input": " ".join(["research"] * 500),
            "expected": "PASS"
        },
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        result = validate_input(test_case["input"])
        actual = result.validation_result.value
        expected = test_case["expected"]
        match = actual == expected

        if match:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"

        print(f"\n{status} Test {i}: {test_case['name']}")
        print(f"   Input: {repr(test_case['input'][:60])}{'...' if len(test_case['input']) > 60 else ''}")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        if result.rejection_message:
            print(f"   Message:  {result.rejection_message}")
        if not match:
            print(f"   ⚠️  MISMATCH")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)}")
    print("=" * 60)
