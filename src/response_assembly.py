"""
Response Assembly (CODE)

Assembles ordered display blocks from pipeline results. This is the single
source of truth for all user-facing static copy and block ordering.

Implements spec lines 875-916: emergency block, main content, healthcare
reminder, footer. The UI renders these blocks without hardcoding any
safety-critical copy.

Block ordering per spec lines 904-910:
1. [Emergency block] <- only if emergency_language_detected == true
2. [Main content]    <- confirmed_prompt, clarification_options, or redirect_message
3. [Healthcare reminder] <- only if include_healthcare_reminder == true
4. [Footer]          <- CONFIRMATION and CLARIFICATION only (not OUT_OF_SCOPE)
"""
from typing import List, Dict, Union

from src.schemas import (
    FinalResponseReady,
    FinalResponseUnderspecified,
    FinalResponseOutOfScope,
    ResponseType,
)
from src.constants import (
    EMERGENCY_WARNING,
    HEALTHCARE_REMINDER,
    FOOTER_CLARIFICATION,
    FOOTER_CONFIRMATION,
)


def assemble_display_blocks(
    response: Union[FinalResponseReady, FinalResponseUnderspecified, FinalResponseOutOfScope]
) -> List[Dict[str, str]]:
    """
    Assemble ordered display blocks from a final pipeline response.

    Args:
        response: One of the three final response types from the pipeline

    Returns:
        List of display blocks, each with 'type' and 'content' keys.
        The UI renders these in order without hardcoding any copy.

    Block types:
    - emergency_warning: Red/amber banner (only if emergency_language_detected)
    - main_content: Response-type-specific content (varies by path)
    - healthcare_reminder: Muted info block (only if include_healthcare_reminder)
    - footer: Subtle text at bottom (CONFIRMATION and CLARIFICATION only)
    """
    blocks = []

    # Block 1: Emergency warning (prepend if flagged)
    if response.emergency_language_detected:
        blocks.append({
            "type": "emergency_warning",
            "content": EMERGENCY_WARNING
        })

    # Block 2: Main content (varies by response_type)
    if response.response_type == ResponseType.CONFIRMATION:
        # CONFIRMATION: confirmed_prompt in a blockquote
        blocks.append({
            "type": "main_content",
            "content": response.confirmed_prompt,
            "subtype": "confirmation"
        })
    elif response.response_type == ResponseType.CLARIFICATION:
        # CLARIFICATION: reasoning + clarification_options as structured data
        # The UI will render these as clickable cards
        blocks.append({
            "type": "main_content",
            "content": {
                "reasoning": response.reasoning,
                "clarification_options": [
                    {
                        "label": opt.label,
                        "rewritten_question": opt.rewritten_question
                    }
                    for opt in response.clarification_options
                ]
            },
            "subtype": "clarification"
        })
    elif response.response_type == ResponseType.OUT_OF_SCOPE:
        # OUT_OF_SCOPE: redirect_message
        blocks.append({
            "type": "main_content",
            "content": response.redirect_message,
            "subtype": "out_of_scope"
        })

    # Block 3: Healthcare reminder (append if flagged)
    # Only READY and UNDERSPECIFIED have this field (OUT_OF_SCOPE doesn't run Call 2)
    if hasattr(response, 'include_healthcare_reminder') and response.include_healthcare_reminder:
        blocks.append({
            "type": "healthcare_reminder",
            "content": HEALTHCARE_REMINDER
        })

    # Block 4: Footer (append for CONFIRMATION and CLARIFICATION only)
    if response.response_type == ResponseType.CONFIRMATION:
        blocks.append({
            "type": "footer",
            "content": FOOTER_CONFIRMATION
        })
    elif response.response_type == ResponseType.CLARIFICATION:
        blocks.append({
            "type": "footer",
            "content": FOOTER_CLARIFICATION
        })
    # No footer for OUT_OF_SCOPE

    return blocks


if __name__ == "__main__":
    """Standalone test runner for response assembly."""
    from src.schemas import (
        PipelineSummary,
        ClarificationOption,
        OutOfScopeReason,
        SecurityType,
    )
    from datetime import datetime
    import json

    print("=" * 70)
    print("Response Assembly Test")
    print("=" * 70)

    # Test 1: CONFIRMATION with emergency + healthcare reminder
    print("\n--- Test 1: CONFIRMATION (emergency + healthcare) ---")
    response1 = FinalResponseReady(
        question_id="test-1",
        response_type=ResponseType.CONFIRMATION,
        original_question="I'm having chest pain, what does research say about it?",
        confirmed_prompt="I'm having chest pain, what does research say about it?",
        include_healthcare_reminder=True,
        emergency_language_detected=True,
        pipeline_summary=PipelineSummary(
            calls_made=2,
            call_1_result="IN_SCOPE",
            call_2_result="READY"
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    blocks1 = assemble_display_blocks(response1)
    print(f"Blocks: {len(blocks1)}")
    for i, block in enumerate(blocks1, 1):
        print(f"  {i}. {block['type']}: {block['content'][:60] if isinstance(block['content'], str) else 'structured data'}...")
    assert len(blocks1) == 4, "Should have 4 blocks: emergency, main, healthcare, footer"
    assert blocks1[0]['type'] == 'emergency_warning'
    assert blocks1[1]['type'] == 'main_content'
    assert blocks1[2]['type'] == 'healthcare_reminder'
    assert blocks1[3]['type'] == 'footer'
    print("✅ All assertions passed")

    # Test 2: CLARIFICATION without emergency or healthcare
    print("\n--- Test 2: CLARIFICATION (no emergency, no healthcare) ---")
    response2 = FinalResponseUnderspecified(
        question_id="test-2",
        response_type=ResponseType.CLARIFICATION,
        original_question="What about vitamin D?",
        triggered_rules=["missing_population", "missing_scope"],
        reasoning="Missing population and scope context",
        clarification_options=[
            ClarificationOption(label="For bone health", rewritten_question="What does research say about vitamin D for bone health in adults?"),
            ClarificationOption(label="For immune function", rewritten_question="What does research say about vitamin D for immune function?"),
        ],
        include_healthcare_reminder=False,
        emergency_language_detected=False,
        pipeline_summary=PipelineSummary(
            calls_made=3,
            call_1_result="IN_SCOPE",
            call_2_result="UNDERSPECIFIED",
            call_2_triggered_rules=["missing_population", "missing_scope"]
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    blocks2 = assemble_display_blocks(response2)
    print(f"Blocks: {len(blocks2)}")
    for i, block in enumerate(blocks2, 1):
        print(f"  {i}. {block['type']}: {block['content'][:60] if isinstance(block['content'], str) else 'structured data'}...")
    assert len(blocks2) == 2, "Should have 2 blocks: main, footer"
    assert blocks2[0]['type'] == 'main_content'
    assert blocks2[0]['subtype'] == 'clarification'
    assert blocks2[1]['type'] == 'footer'
    assert blocks2[1]['content'] == FOOTER_CLARIFICATION
    print("✅ All assertions passed")

    # Test 3: OUT_OF_SCOPE (no footer, no healthcare, no emergency)
    print("\n--- Test 3: OUT_OF_SCOPE (minimal) ---")
    response3 = FinalResponseOutOfScope(
        question_id="test-3",
        response_type=ResponseType.OUT_OF_SCOPE,
        original_question="What's the weather?",
        out_of_scope_reason=OutOfScopeReason.NON_MEDICAL,
        security_type=SecurityType.NONE,
        redirect_message="This tool is designed for medical research questions.",
        emergency_language_detected=False,
        pipeline_summary=PipelineSummary(
            calls_made=1,
            call_1_result="OUT_OF_SCOPE"
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    blocks3 = assemble_display_blocks(response3)
    print(f"Blocks: {len(blocks3)}")
    for i, block in enumerate(blocks3, 1):
        print(f"  {i}. {block['type']}: {block['content'][:60] if isinstance(block['content'], str) else 'structured data'}...")
    assert len(blocks3) == 1, "Should have 1 block: main only"
    assert blocks3[0]['type'] == 'main_content'
    assert blocks3[0]['subtype'] == 'out_of_scope'
    print("✅ All assertions passed")

    # Test 4: CONFIRMATION with only healthcare (no emergency)
    print("\n--- Test 4: CONFIRMATION (healthcare only) ---")
    response4 = FinalResponseReady(
        question_id="test-4",
        response_type=ResponseType.CONFIRMATION,
        original_question="What does research say about my FSH levels?",
        confirmed_prompt="What does research say about my FSH levels?",
        include_healthcare_reminder=True,
        emergency_language_detected=False,
        pipeline_summary=PipelineSummary(
            calls_made=2,
            call_1_result="IN_SCOPE",
            call_2_result="READY"
        ),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    blocks4 = assemble_display_blocks(response4)
    print(f"Blocks: {len(blocks4)}")
    for i, block in enumerate(blocks4, 1):
        print(f"  {i}. {block['type']}: {block['content'][:60] if isinstance(block['content'], str) else 'structured data'}...")
    assert len(blocks4) == 3, "Should have 3 blocks: main, healthcare, footer"
    assert blocks4[0]['type'] == 'main_content'
    assert blocks4[1]['type'] == 'healthcare_reminder'
    assert blocks4[2]['type'] == 'footer'
    print("✅ All assertions passed")

    print("\n" + "=" * 70)
    print("All tests passed!")
    print("=" * 70)
