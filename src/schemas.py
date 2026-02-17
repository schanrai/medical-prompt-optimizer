"""
Pydantic schemas for Medical Research Prompt Optimizer v1.

All input/output schemas from the specification.
"""
from enum import Enum
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# Enums for type safety
class ValidationResult(str, Enum):
    PASS = "PASS"
    REJECT_EMPTY = "REJECT_EMPTY"
    REJECT_TOO_SHORT = "REJECT_TOO_SHORT"
    REJECT_TOO_LONG = "REJECT_TOO_LONG"
    REJECT_GIBBERISH = "REJECT_GIBBERISH"


class SecurityType(str, Enum):
    NONE = "NONE"
    INJECTION = "INJECTION"
    JAILBREAK = "JAILBREAK"
    EXTRACTION = "EXTRACTION"


class ScopeResult(str, Enum):
    IN_SCOPE = "IN_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class OutOfScopeReason(str, Enum):
    NON_ENGLISH = "NON_ENGLISH"
    NON_MEDICAL = "NON_MEDICAL"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    DRUG_SEEKING = "DRUG_SEEKING"


class Classification(str, Enum):
    UNDERSPECIFIED = "UNDERSPECIFIED"
    READY = "READY"


class ResponseType(str, Enum):
    CONFIRMATION = "CONFIRMATION"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class RoutingDecision(str, Enum):
    SECURITY_VIOLATION = "security_violation"
    NON_MEDICAL = "non_medical"
    NON_ENGLISH = "non_english"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"


# Stage 0: Code Input Validation
class ValidationResultModel(BaseModel):
    question_id: str
    validation_result: ValidationResult
    rejection_message: Optional[str] = None
    timestamp: str


# Call 1: Scope + Security Gate
class Call1Response(BaseModel):
    question_id: str
    call: Literal[1] = 1
    is_english: bool
    is_medical: bool
    security_violation: bool
    security_type: SecurityType
    emergency_language_detected: bool
    self_harm_language_detected: bool
    drug_seeking_detected: bool
    reasoning: str
    scope_result: ScopeResult
    out_of_scope_reason: Optional[OutOfScopeReason] = None
    model_used: str
    token_count: int
    latency_ms: int
    timestamp: str


# Call 2: Classification
class Call2Response(BaseModel):
    question_id: str
    call: Literal[2] = 2
    classification: Classification
    triggered_rules: List[str] = Field(default_factory=list)
    reasoning: str
    personal_health_referenced: bool
    model_used: str
    token_count: int
    latency_ms: int
    timestamp: str


# Call 3: Clarification Generator
class ClarificationOption(BaseModel):
    label: str = Field(..., description="2-5 words describing the angle")
    rewritten_question: str = Field(..., description="Standalone question user can use directly")


class Call3Response(BaseModel):
    question_id: str
    call: Literal[3] = 3
    clarification_options: List[ClarificationOption] = Field(..., min_length=2, max_length=4)
    reasoning: str
    model_used: str
    token_count: int
    latency_ms: int
    timestamp: str


# Final Response Schemas
class PipelineSummary(BaseModel):
    calls_made: int
    call_1_result: str
    call_2_result: Optional[str] = None
    call_2_triggered_rules: Optional[List[str]] = None


class FinalResponseReady(BaseModel):
    question_id: str
    response_type: Literal[ResponseType.CONFIRMATION] = ResponseType.CONFIRMATION
    original_question: str
    confirmed_prompt: str
    include_healthcare_reminder: bool
    emergency_language_detected: bool = False
    self_harm_language_detected: bool = False
    drug_seeking_detected: bool = False
    pipeline_summary: PipelineSummary
    timestamp: str


class FinalResponseUnderspecified(BaseModel):
    question_id: str
    response_type: Literal[ResponseType.CLARIFICATION] = ResponseType.CLARIFICATION
    original_question: str
    triggered_rules: List[str]
    reasoning: str
    clarification_options: List[ClarificationOption]
    include_healthcare_reminder: bool
    emergency_language_detected: bool = False
    self_harm_language_detected: bool = False
    drug_seeking_detected: bool = False
    pipeline_summary: PipelineSummary
    timestamp: str


class FinalResponseOutOfScope(BaseModel):
    question_id: str
    response_type: Literal[ResponseType.OUT_OF_SCOPE] = ResponseType.OUT_OF_SCOPE
    original_question: str
    out_of_scope_reason: OutOfScopeReason
    security_type: SecurityType
    redirect_message: str
    emergency_language_detected: bool = False
    self_harm_language_detected: bool = False
    drug_seeking_detected: bool = False
    pipeline_summary: PipelineSummary
    timestamp: str


# Telemetry Entry
class TelemetryEntry(BaseModel):
    question_id: str
    raw_input: str
    input_hash: str
    classification_result: Literal["OUT_OF_SCOPE", "UNDERSPECIFIED", "READY"]
    routing_decision: RoutingDecision
    triggered_rules: List[str] = Field(default_factory=list)
    prompt_version: str
    model_version: str
    token_count: int
    latency_ms: int
    timestamp: str
    outcome: Literal["clarification_options", "confirmed_prompt", "out_of_scope_redirect"]
