# Running the FastAPI Server

## Phase 3: REST API

The Medical Research Prompt Optimizer now includes a REST API for processing medical research questions.

---

## Quick Start

### 1. Activate virtual environment
```bash
cd medical-prompt-optimizer
source venv/bin/activate
```

### 2. Install dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### 3. Start the server
```bash
uvicorn src.app:app --reload
```

The API will be available at: **http://localhost:8000**

---

## Endpoints

### `GET /`
Web interface (placeholder until Phase 4 UI is built)

### `POST /api/check`
Process a medical research question through the pipeline

**Request:**
```json
{
  "question": "What does research say about vitamin D for bone health?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "question_id": "uuid",
    "response_type": "CLARIFICATION",
    "original_question": "...",
    "clarification_options": [...],
    "pipeline_summary": {...}
  }
}
```

### `GET /health`
Health check endpoint

### `GET /api/info`
API information and capabilities

---

## Testing the API

### Option 1: Test Script (Recommended)
```bash
# In terminal 1: Start the server
uvicorn src.app:app --reload

# In terminal 2: Run tests
python test_api.py
```

### Option 2: curl
```bash
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"question": "What does research say about vitamin D for bone health?"}'
```

### Option 3: Python requests
```python
import requests

response = requests.post(
    "http://localhost:8000/api/check",
    json={"question": "What does research say about vitamin D for bone health?"}
)

result = response.json()
print(result)
```

### Option 4: Browser
1. Open http://localhost:8000 to see API status
2. Open http://localhost:8000/docs for interactive API documentation (Swagger UI)
3. Open http://localhost:8000/redoc for alternative API docs

---

## Response Types

The pipeline can return three response types:

### 1. OUT_OF_SCOPE
Question is not a medical research question or contains security violations
```json
{
  "response_type": "OUT_OF_SCOPE",
  "out_of_scope_reason": "NON_MEDICAL",
  "redirect_message": "..."
}
```

### 2. CONFIRMATION (READY)
Question is well-formed and ready to use
```json
{
  "response_type": "CONFIRMATION",
  "confirmed_prompt": "...",
  "include_healthcare_reminder": false
}
```

### 3. CLARIFICATION (UNDERSPECIFIED)
Question needs clarification - returns 2-4 rewrite options
```json
{
  "response_type": "CLARIFICATION",
  "triggered_rules": ["missing_population", "requests_conclusion"],
  "clarification_options": [
    {
      "label": "Population-specific",
      "rewritten_question": "..."
    }
  ],
  "include_healthcare_reminder": false
}
```

---

## Development

### Auto-reload
The `--reload` flag enables auto-reload on code changes. The server will restart automatically when you edit Python files.

### Logs
Server logs appear in the terminal where you ran `uvicorn`. Look for:
- Request logs: `INFO: Received question: ...`
- Pipeline results: `INFO: Pipeline result: UNDERSPECIFIED, calls_made=3`
- Errors: `ERROR: Pipeline error: ...`

### Port Configuration
To use a different port:
```bash
uvicorn src.app:app --reload --port 8080
```

---

## Next: Phase 4 (UI)

Phase 4 will add:
- HTML form interface at `GET /`
- Tailwind CSS styling
- JavaScript for form submission
- User-friendly display of results

The API backend is ready and waiting for the UI layer!
