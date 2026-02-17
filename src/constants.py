"""
Constants for Medical Research Prompt Optimizer v1.

Static copy strings, model configuration, and prompt version tracking.
All environment and path config moved to src/config.py.
"""

# Prompt version (tracked in telemetry)
PROMPT_VERSION = "v1.0"

# Model configuration per call (from spec testing results, lines 88-99)
CALL_1_MODEL = "anthropic/claude-sonnet-4-5"  # Scope + Security Gate
CALL_1_PARAMS = {
    "temperature": 0.0,  # Deterministic gate-keeping
}

CALL_2_MODEL = "anthropic/claude-sonnet-4-5"    # Classification
CALL_2_PARAMS = {
    "temperature": 0.1,  # Deterministic classification (medical safety)
}

CALL_3_MODEL = "anthropic/claude-sonnet-4-5"  # Clarification Generator
CALL_3_PARAMS = {
    "temperature": 0.3,  # Deterministic clarification generation
}

# Static copy strings (from spec lines 1030-1037 + Phase 4 decisions)
EMERGENCY_WARNING = """⚠️ URGENT: If you're experiencing a medical emergency, call 911 immediately.
For poison emergencies, call Poison Control: 1-800-222-1222."""

SELF_HARM_WARNING = """🆘 CRISIS SUPPORT: If you're thinking about suicide or self-harm, help is available 24/7.

988 Suicide & Crisis Lifeline: Call or text 988
Crisis Text Line: Text HOME to 741741

You are not alone. Trained counselors are ready to listen."""

DRUG_SEEKING_REJECTION = "This tool is designed for general medical research questions, not medication access requests."

DRUG_SEEKING_SUPPORT = """If you're struggling with substance use, confidential help is available:

SAMHSA National Helpline: 1-800-662-4357 (24/7, free, confidential)
This service provides referrals to local treatment facilities and support groups."""

HEALTHCARE_REMINDER = "If you're experiencing symptoms, please consult a healthcare provider."

# Per-response-type footers (decided in Phase 4 planning)
FOOTER_CLARIFICATION = "Pick or revise, then use with your preferred research tool or LLM chatbot."
FOOTER_CONFIRMATION = "Your question can be used safely with your preferred research tool or LLM chatbot."
# No footer for OUT_OF_SCOPE -- redirect messages are self-contained

# Privacy and page-level copy
PRIVACY_NOTICE = "Your questions are processed securely and are not stored or used for AI model training."
PAGE_DISCLAIMER = "This tool does not answer questions or provide medical advice. It helps you frame better research prompts."

# OUT_OF_SCOPE response templates (from spec lines 524-551)
OUT_OF_SCOPE_SECURITY = """This tool is designed to help frame medical research questions.

Your input appears to contain instructions that don't align with this purpose.
Please submit a medical research question you'd like help framing."""

OUT_OF_SCOPE_NON_ENGLISH = """This tool currently supports English-language questions only.

Please resubmit your medical research question in English."""

OUT_OF_SCOPE_NON_MEDICAL = """This tool is designed for medical research questions.

Your question doesn't appear to be health-related. If it is, try rephrasing
to make the health/medical topic clearer.

Examples of medical research questions this tool can help with:
- "What does the research say about [supplement/treatment] for [condition]?"
- "How do [biomarker] levels vary across [populations]?"
- "What are the known risks of [intervention] in [population]?"""
