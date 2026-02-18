# Medical Prompt Optimizer

A production-grade system for transforming ambiguous medical research questions into structured, safe prompts through a three-stage clarification pipeline.

## Purpose

Medical research queries often contain ambiguity, security risks, or crisis language that requires careful handling. This system validates inputs, detects security violations and crisis situations, classifies question quality, and guides users toward well-formed prompts before research assistance is provided.

**Key Constraint:** Medical domain = high stakes. System clarifies rather than guesses, and flags crisis situations while continuing to help.

## Architecture

### Three-Call Pipeline

**Stage 0: Code Input Validation** (Pre-LLM)
- Length validation (3-500 words)
- Non-empty check
- Fails fast before LLM calls

**Call 1: Scope + Security Gate** (`call_1_scope.py`)
- Language detection (English-only)
- Medical topic verification
- Security violation detection (injection, jailbreak, extraction)
- Pasted medical document detection
- **Crisis detection:** Emergency language, self-harm/suicidal ideation, drug-seeking behavior
- Routes OUT_OF_SCOPE if violations detected; flags crises and continues pipeline otherwise

**Call 2: Classification** (`call_2_classify.py`)
- Evaluates question against three rule sets:
  1. **Intent Clarity:** intent_ambiguous, multi_intent, undefined_criteria
  2. **Structural Completeness:** missing_population, missing_scope
  3. **Epistemic Validity:** assumes_causation, requests_conclusion, embedded_assumption
- Returns READY (no clarification needed) or UNDERSPECIFIED (triggers Call 3)

**Call 3: Clarification Generator** (`call_3_clarify.py`)
- Generates 2-4 rewritten question options addressing triggered rules
- Each option is standalone and ready to use
- User can select one or revise their original question

### Model Configuration

- **Call 1:** `anthropic/claude-sonnet-4-5` (temp 0.0) - Deterministic gate-keeping
- **Call 2:** `anthropic/claude-sonnet-4-6` (temp 0.1) - Enhanced classification with better rule discernment
- **Call 3:** `anthropic/claude-sonnet-4-5` (temp 0.3) - Creative clarification generation

### Core Components

- **Pipeline** (`pipeline.py`): Orchestrates all three calls with telemetry
- **LLM Client** (`llm_client.py`): OpenRouter API wrapper with structured output support
- **Schemas** (`schemas.py`): Type-safe Pydantic models for all responses
- **JSON Schemas** (`json_schemas.py`): Structured output schemas for reliable JSON responses
- **Validation** (`validation.py`): Stage 0 code validation (length, emptiness)
- **Config** (`config.py`): Environment-based configuration
- **Constants** (`constants.py`): Static copy, model config, prompt version tracking
- **Telemetry** (`telemetry.py`): Structured logging with run tracking
- **Exceptions** (`exceptions.py`): Domain-specific error handling

### Web Interface

- **FastAPI App** (`app.py`): REST API with CORS support
- **Frontend** (`index.html`): Single-page interface for question submission
- **API Endpoint:** `POST /api/check` - Returns classification and clarification options

## Setup

### Prerequisites

- Python 3.9+
- OpenRouter API key
- Supabase project (optional, for persistence)

### Installation

```bash
# Clone and navigate to project
cd medical-prompt-optimizer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional (defaults provided)
OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions
HTTP_TIMEOUT=60.0
```

## Running the System

### Start the Web Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start FastAPI server with auto-reload
python -m uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# Access at http://localhost:8000
```

### Test the Pipeline

```bash
# Run comprehensive corpus test (28 questions)
python test_corpus.py

# Test individual calls
python -m src.call_1_scope
python -m src.call_2_classify
python -m src.call_3_clarify

# Test full pipeline
python -m src.pipeline
```

## Testing

The system includes a comprehensive test corpus (`test_corpus.py`) with 28 questions covering:

- **Happy Path (3):** Well-formed questions that are READY
- **Clean Edge Cases (7):** Ambiguous but well-formatted questions
- **Messy Edge Cases (7):** Real-world messy input with typos, formatting issues
- **Adversarial (5):** Security probes, jailbreak attempts, prompt injection
- **Crisis Detection (6):** Self-harm, drug-seeking, and false positive checks

**Current Test Results:** 28/28 passed (100%) ✅

## Project Structure

```
medical-prompt-optimizer/
├── src/
│   ├── pipeline.py           # Main pipeline orchestration
│   ├── call_1_scope.py       # Call 1: Scope + Security Gate
│   ├── call_2_classify.py    # Call 2: Classification
│   ├── call_3_clarify.py     # Call 3: Clarification Generator
│   ├── llm_client.py          # OpenRouter API client
│   ├── schemas.py             # Pydantic response models
│   ├── json_schemas.py        # Structured output schemas
│   ├── validation.py          # Stage 0 code validation
│   ├── config.py              # Environment configuration
│   ├── constants.py           # Static copy and model config
│   ├── telemetry.py           # Structured logging
│   ├── exceptions.py          # Error handling
│   └── app.py                 # FastAPI web server
├── prompts/
│   ├── call_1_system.txt      # Scope + security gate prompt
│   ├── call_2_system.txt      # Classification prompt
│   └── call_3_system.txt      # Clarification generation prompt
├── static/
│   ├── index.html             # Web interface
│   └── styles.css             # UI styling
├── test_corpus.py             # Comprehensive test suite
├── requirements.txt
└── README.md
```

## Key Features

### Crisis Detection
- **Self-Harm Detection:** Flags suicidal ideation while continuing to provide research help + 988 resources
- **Drug-Seeking Detection:** Routes prescription access requests to SAMHSA helpline
- **Emergency Detection:** Identifies active medical crises and displays 911/Poison Control guidance
- **False Positive Avoidance:** Research questions about suicide prevention or medication classes don't trigger crisis flags

### Security
- **Injection Detection:** Blocks "ignore previous instructions" and similar attacks
- **Jailbreak Prevention:** Rejects roleplay requests and urgency manipulation
- **Extraction Blocking:** Refuses system prompt disclosure attempts

### Classification Intelligence
- **Threshold Tests:** Rules include qualifying gates (e.g., "Would the answer materially change for different sub-populations?")
- **Evidence Framing Recognition:** "What does research say about X" is recognized as valid evidence framing
- **Flexible Matching:** READY vs UNDERSPECIFIED based on structural completeness, not surface polish

## Development Principles

This project follows production-ready coding standards from the start:

- **Type Safety**: Comprehensive type hints on all functions
- **Validation**: Pydantic models for all data structures
- **Structured Output**: JSON schemas ensure reliable LLM responses
- **Error Handling**: Explicit exception classes and informative messages
- **Logging**: Structured telemetry with run tracking and input hashing
- **Configuration**: Environment-based, never hardcoded
- **Extensibility**: Dependency injection, parameter dicts, config objects
- **Modern Python**: pathlib, dataclasses/Pydantic, f-strings, async-ready (httpx)


## License

Educational project - part of AI PM learning curriculum.
