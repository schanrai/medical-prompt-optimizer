"""
Medical Research Prompt Optimizer - FastAPI Application

Phase 3: REST API for the Medical Prompt Optimizer pipeline.

Endpoints:
- GET /: Serves the HTML form UI (Phase 4)
- POST /api/check: Processes medical research questions through the pipeline
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pathlib import Path
import logging
import os

from src.pipeline import run_pipeline
from src.response_assembly import assemble_display_blocks
from src.exceptions import MPOError
from src.schemas import ResponseType, ValidationResultModel, ValidationResult
from src.constants import PRIVACY_NOTICE, PAGE_DISCLAIMER

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

# Create templates directory if it doesn't exist
TEMPLATES_DIR.mkdir(exist_ok=True)

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
    
    Passes static copy constants to the template for rendering.
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "privacy_notice": PRIVACY_NOTICE,
        "page_disclaimer": PAGE_DISCLAIMER
    })


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """
    Serve the privacy policy page.
    """
    return templates.TemplateResponse("privacy.html", {
        "request": request
    })


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


# Local dev: mount public/ at root so /styles.css and /main.js resolve correctly.
# Must be added AFTER all routes so explicit routes take priority over the mount.
# On Vercel (VERCEL=1), skipped entirely — CDN serves public/ automatically.
if not os.getenv("VERCEL"):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=BASE_DIR / "public"), name="public")


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
