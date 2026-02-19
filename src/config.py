"""
Configuration management for Medical Research Prompt Optimizer.

Centralized paths, environment variables, and runtime configuration.
Production-ready: validates config on import, fails fast if misconfigured.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from src.exceptions import ConfigurationError

# Load environment variables
load_dotenv()

# Project root (where this file lives is src/, parent is project root)
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure critical directories exist (skip on read-only filesystem, e.g. Vercel)
try:
    LOGS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
except OSError:
    pass  # read-only env: telemetry will skip file writes

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ConfigurationError(
        "OPENROUTER_API_KEY not found in environment. "
        "Create a .env file with OPENROUTER_API_KEY=your_key_here"
    )

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# HTTP client configuration
HTTP_TIMEOUT = 60.0  # seconds
MAX_RETRIES = 0  # v1: no retries, fail fast

# Telemetry
TELEMETRY_FILE = LOGS_DIR / "telemetry.jsonl"
