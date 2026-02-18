"""
JSON schemas for structured output validation.

OpenRouter supports response_format parameter with json_schema for reliable JSON responses.
These schemas ensure API responses match expected structure exactly.
"""

# Call 1: Scope + Security Gate
CALL_1_SCHEMA = {
    "type": "object",
    "properties": {
        "is_english": {
            "type": "boolean",
            "description": "Whether the input is in English"
        },
        "is_medical": {
            "type": "boolean",
            "description": "Whether the input is about a medical/health topic"
        },
        "pasted_medical_documents": {
            "type": "boolean",
            "description": "Whether the input is primarily pasted medical documents (lab results, test reports, records) requesting interpretation of personal results"
        },
        "security_violation": {
            "type": "boolean",
            "description": "Whether the input contains injection/jailbreak/extraction attempts"
        },
        "security_type": {
            "type": "string",
            "enum": ["NONE", "INJECTION", "JAILBREAK", "EXTRACTION"],
            "description": "Type of security violation if detected"
        },
        "emergency_language_detected": {
            "type": "boolean",
            "description": "Whether the user appears to be in an active medical crisis right now"
        },
        "self_harm_language_detected": {
            "type": "boolean",
            "description": "Whether input expresses suicidal ideation or self-harm intent"
        },
        "drug_seeking_detected": {
            "type": "boolean",
            "description": "Whether input requests medication access without prescription"
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of the classification decision"
        }
    },
    "required": ["is_english", "is_medical", "pasted_medical_documents", "security_violation", "security_type", "emergency_language_detected", "self_harm_language_detected", "drug_seeking_detected", "reasoning"],
    "additionalProperties": False
}

# Call 2: Classification
CALL_2_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["UNDERSPECIFIED", "READY"],
            "description": "Whether question is structurally complete (READY) or needs clarification (UNDERSPECIFIED)"
        },
        "triggered_rules": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "intent_ambiguous",
                    "missing_population",
                    "missing_scope",
                    "assumes_causation",
                    "requests_conclusion",
                    "embedded_assumption",
                    "multi_intent",
                    "undefined_criteria"
                ]
            },
            "description": "List of rule IDs that were triggered (empty if READY)"
        },
        "reasoning": {
            "type": "string",
            "description": "Explanation of why rules were triggered or why question is READY"
        },
        "personal_health_referenced": {
            "type": "boolean",
            "description": "Whether the question references personal health situation"
        }
    },
    "required": ["classification", "triggered_rules", "reasoning", "personal_health_referenced"],
    "additionalProperties": False
}

# Call 3: Clarification Generator
# Note: minItems/maxItems not supported by Anthropic's structured output
# Validation of 2-4 items must be done in code after response
CALL_3_SCHEMA = {
    "type": "object",
    "properties": {
        "clarification_options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "2-5 word description of this rewrite angle"
                    },
                    "rewritten_question": {
                        "type": "string",
                        "description": "Standalone question user can select and use directly"
                    }
                },
                "required": ["label", "rewritten_question"],
                "additionalProperties": False
            },
            "description": "Array of 2-4 rewrite options addressing the triggered rules"
        },
        "reasoning": {
            "type": "string",
            "description": "Explanation of which triggered rules were addressed and how"
        }
    },
    "required": ["clarification_options", "reasoning"],
    "additionalProperties": False
}
