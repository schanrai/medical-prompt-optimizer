"""
Medical Research Prompt Optimizer - FastAPI Application

Phase 3: REST API for the Medical Prompt Optimizer pipeline.

Endpoints:
- GET /: Serves the HTML form UI (Phase 4)
- POST /api/check: Processes medical research questions through the pipeline
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pathlib import Path
import logging

from src.pipeline import run_pipeline
from src.response_assembly import assemble_display_blocks
from src.exceptions import MPOError
from src.schemas import ResponseType, ValidationResultModel, ValidationResult

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Medical Research Prompt Optimizer",
    description="Transform ambiguous medical research questions into structured, safe prompts",
    version="1.0.0"
)

# Setup paths
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Request/Response models
class QuestionRequest(BaseModel):
    """Request model for /api/check endpoint.
    
    No length constraints here -- Stage 0 validation in the pipeline handles
    length checks with user-friendly rejection messages instead of raw 422 errors.
    """
    question: str = Field(..., description="Medical research question to optimize")


class APIResponse(BaseModel):
    """Standardized API response wrapper."""
    success: bool
    data: dict = None
    error: str = None


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Serve the HTML form UI.
    
    Phase 4 will populate templates/index.html.
    For now, return a basic placeholder.
    """
    # Check if index.html exists
    index_path = TEMPLATES_DIR / "index.html"
    
    if index_path.exists():
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        # Placeholder until Phase 4
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Medical Research Prompt Optimizer</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 50px auto; 
                    padding: 20px;
                }
                .info { 
                    background: #e3f2fd; 
                    padding: 20px; 
                    border-radius: 8px; 
                    border-left: 4px solid #2196f3;
                }
                code { 
                    background: #f5f5f5; 
                    padding: 2px 6px; 
                    border-radius: 3px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <h1>Medical Research Prompt Optimizer</h1>
            <div class="info">
                <h2>API is Running ✓</h2>
                <p>Phase 3 complete! The FastAPI backend is ready.</p>
                <p><strong>API Endpoint:</strong> <code>POST /api/check</code></p>
                <p><strong>Example request:</strong></p>
                <pre><code>{
  "question": "What does research say about vitamin D for bone health?"
}</code></pre>
                <p><strong>Phase 4 (UI):</strong> Coming soon - HTML form interface will be added here.</p>
                <p>For now, you can test the API using:</p>
                <ul>
                    <li>curl</li>
                    <li>Postman</li>
                    <li>Python requests</li>
                    <li>The interactive test script: <code>python test_interactive.py</code></li>
                </ul>
            </div>
        </body>
        </html>
        """)


@app.post("/api/check", response_model=APIResponse)
async def check_question(request: QuestionRequest):
    """
    Process a medical research question through the pipeline.
    
    Args:
        request: QuestionRequest containing the user's question
    
    Returns:
        APIResponse with pipeline results or error
    
    Response structure depends on pipeline path:
    - OUT_OF_SCOPE: redirect message and reason
    - READY: confirmed prompt
    - UNDERSPECIFIED: clarification options
    """
    try:
        logger.info(f"Received question: {request.question[:100]}...")
        
        # Run through pipeline (includes Stage 0 validation)
        result = run_pipeline(request.question)
        
        # Check if Stage 0 rejected the input
        if isinstance(result, ValidationResultModel):
            logger.info(f"Stage 0 rejected: {result.validation_result.value}")
            return APIResponse(
                success=False,
                error=result.rejection_message
            )
        
        # Assemble display blocks from pipeline result
        display_blocks = assemble_display_blocks(result)
        
        # Convert Pydantic model to dict for JSON response
        result_dict = result.model_dump()
        
        # Add display_blocks to the response
        result_dict['display_blocks'] = display_blocks
        
        # Log result type
        logger.info(f"Pipeline result: {result.response_type.value}, calls_made={result.pipeline_summary.calls_made}, blocks={len(display_blocks)}")
        
        return APIResponse(
            success=True,
            data=result_dict
        )
        
    except MPOError as e:
        # Pipeline-specific error (LLM call failed, JSON parse error, etc.)
        logger.error(f"Pipeline error: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": type(e).__name__,
                "message": str(e)
            }
        )
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "InternalServerError",
                "message": "An unexpected error occurred processing your request"
            }
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring/deployment.
    
    Returns:
        Simple status response
    """
    return {"status": "healthy", "service": "medical-prompt-optimizer", "version": "1.0.0"}


@app.get("/api/info")
async def api_info():
    """
    API information endpoint.
    
    Returns:
        API capabilities and response type schemas
    """
    return {
        "service": "Medical Research Prompt Optimizer",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/check": "Process medical research question",
            "GET /health": "Health check",
            "GET /api/info": "API information"
        },
        "response_types": {
            "OUT_OF_SCOPE": "Question is not a medical research question or contains security violations",
            "READY": "Question is well-formed and ready to use",
            "UNDERSPECIFIED": "Question needs clarification - returns 2-4 rewrite options"
        },
        "pipeline": {
            "call_1": "Scope + Security Gate",
            "call_2": "Classification",
            "call_3": "Clarification Generator (if needed)"
        }
    }


if __name__ == "__main__":
    """Run the app with uvicorn for development."""
    import uvicorn
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
