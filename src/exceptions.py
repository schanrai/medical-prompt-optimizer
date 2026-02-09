"""
Custom exceptions for Medical Research Prompt Optimizer.

Production-grade error handling with clear exception hierarchy.
"""


class MPOError(Exception):
    """Base exception for all Medical Prompt Optimizer errors."""
    pass


class LLMCallError(MPOError):
    """Raised when an LLM API call fails."""
    def __init__(self, message: str, model: str, status_code: int = None, response_text: str = None):
        self.model = model
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"LLM call failed (model={model}): {message}")


class JSONParseError(MPOError):
    """Raised when LLM returns invalid JSON."""
    def __init__(self, raw_response: str, parse_error: str):
        self.raw_response = raw_response
        self.parse_error = parse_error
        super().__init__(f"Failed to parse JSON from LLM response: {parse_error}")


class ValidationError(MPOError):
    """Raised when response validation fails."""
    def __init__(self, message: str, response_data: dict = None):
        self.response_data = response_data
        super().__init__(f"Validation failed: {message}")


class ConfigurationError(MPOError):
    """Raised when configuration is missing or invalid."""
    pass
