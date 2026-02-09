# Medical Prompt Optimizer

A production-grade system for transforming ambiguous medical research questions into structured, safe prompts through a three-stage clarification pipeline.

## Purpose

Medical research queries often contain ambiguity that could lead to unsafe or unhelpful AI responses. This system detects ambiguity, classifies medical domains, and guides users toward well-formed prompts before any research assistance is provided.

**Key Constraint:** Medical domain = high stakes. System clarifies rather than guesses.

## Architecture

### Three-Stage Pipeline

1. **Stage 1: Scope Analysis** (`call_1_scope.py`)
   - Detects ambiguity levels (low/medium/high)
   - Classifies medical domain (clinical, research, education, etc.)
   - Identifies query intent
   - Generates targeted clarifying questions

2. **Stage 2: Evidence Specification** (planned)
   - Refines evidence requirements based on clarifications
   - Establishes quality criteria

3. **Stage 3: Output Requirements** (planned)
   - Defines output format and constraints
   - Sets safety guardrails

### Core Components

- **LLM Client** (`llm_client.py`): Structured API calls with Pydantic validation
- **Schemas** (`schemas.py`): Type-safe data models for all inputs/outputs
- **Config** (`config.py`): Environment-based configuration management
- **Telemetry** (`telemetry.py`): Structured logging for debugging and monitoring
- **Exceptions** (`exceptions.py`): Domain-specific error handling

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
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_SITE_URL=http://localhost:3000
OPENROUTER_APP_NAME=medical-prompt-optimizer

# Supabase (if using persistence)
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```

## Testing

```bash
# Test OpenRouter connection
python test_openrouter.py

# Test Supabase connection (if configured)
python test_supabase.py

# Run Stage 1 with sample query
python -m src.call_1_scope
```

## Project Structure

```
medical-prompt-optimizer/
├── src/
│   ├── call_1_scope.py      # Stage 1: Ambiguity detection
│   ├── llm_client.py         # LLM API client
│   ├── schemas.py            # Pydantic models
│   ├── config.py             # Configuration
│   ├── constants.py          # System constants
│   ├── telemetry.py          # Logging
│   └── exceptions.py         # Error handling
├── prompts/
│   ├── call_1_system.txt     # Stage 1 system prompt
│   ├── call_2_system.txt     # Stage 2 system prompt (planned)
│   └── call_3_system.txt     # Stage 3 system prompt (planned)
├── data/
│   └── input_corpus.json     # Test queries
├── test_openrouter.py        # API connectivity test
├── test_supabase.py          # Database connectivity test
├── requirements.txt
└── README.md
```

## Development Principles

This project follows production-ready coding standards from the start:

- **Type Safety**: Comprehensive type hints on all functions
- **Validation**: Pydantic models for all data structures
- **Error Handling**: Explicit exception classes and informative messages
- **Logging**: Structured telemetry for debugging
- **Configuration**: Environment-based, never hardcoded
- **Extensibility**: Dependency injection, parameter dicts

## Learning Context

Built as part of Week 2 (Prompting Design) in the AI PM Curriculum.

**Learning Objectives:**
- Design prompts for high-stakes domains
- Handle ambiguity conservatively
- Implement structured outputs with validation
- Build production-ready telemetry and error handling

## License

Educational project - part of AI PM learning curriculum.
