from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import nltk
import logging
import os
from contextlib import asynccontextmanager
import asyncio
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SynthesisTalk API...")
    
    # Download NLTK data if needed
    try:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        nltk.download("stopwords", quiet=True)
        nltk.download("averaged_perceptron_tagger", quiet=True)
        logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.warning(f"Could not download NLTK data: {e}")
    
    # Verify environment variables - Updated to match your actual .env file
    required_env_vars = ["NGU_API_KEY", "GROQ_API_KEY"]  # Fixed to match your .env
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
    else:
        logger.info("All required environment variables are present")
    
    # Additional optional variables
    optional_vars = ["NGU_BASE_URL", "NGU_MODEL", "GROQ_BASE_URL", "GROQ_MODEL", "MODEL_SERVER"]
    present_optional = [var for var in optional_vars if os.getenv(var)]
    if present_optional:
        logger.info(f"Optional environment variables configured: {present_optional}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SynthesisTalk API...")

# Import all routers
from backend.routes.upload import router as upload_router
from backend.routes.chat import router as chat_router
from backend.routes.search import router as search_router
from backend.routes.export import router as export_router
from backend.routes.visualize import router as visualize_router
from backend.routes.tools import router as tools_router
from backend.routes.insights import router as insights_router
from backend.routes.context import router as context_router

app = FastAPI(
    title="SynthesisTalk API",
    description="Collaborative Research Assistant - Advanced LLM-powered research tool with document analysis, web search, and intelligent synthesis capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React default
        "http://localhost:5173",   # Vite default
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://127.0.0.1:3000"   # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# **NEW: Add timeout middleware**
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse as StarletteJSONResponse

class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int = 120):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            # Set a timeout for the entire request
            return await asyncio.wait_for(
                call_next(request), 
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {self.timeout}s for {request.url}")
            return StarletteJSONResponse(
                status_code=408,
                content={
                    "detail": f"Request timed out after {self.timeout} seconds",
                    "error_type": "timeout",
                    "suggestion": "Try breaking your request into smaller parts or contact support"
                }
            )

# Add timeout middleware (120 seconds = 2 minutes)
app.add_middleware(TimeoutMiddleware, timeout=120)

# Global exception handler with better timeout handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, asyncio.TimeoutError):
        logger.error(f"Timeout exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=408,
            content={
                "detail": "Request timed out. The operation may be taking longer than expected.",
                "error_type": "timeout",
                "suggestion": "Please try again or break your request into smaller parts"
            }
        )
    
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Register routers with prefixes for better organization
app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(search_router, prefix="/api/v1", tags=["Search"])
app.include_router(export_router, prefix="/api/v1", tags=["Export"])
app.include_router(visualize_router, prefix="/api/v1", tags=["Visualization"])
app.include_router(tools_router, prefix="/api/v1", tags=["Tools"])
app.include_router(insights_router, prefix="/api/v1", tags=["Insights"])
app.include_router(context_router, prefix="/api/v1", tags=["Context"])

@app.get("/")
def root():
    return {
        "message": "SynthesisTalk API is running",
        "status": "healthy",
        "version": "1.0.0",
        "timeout_config": "120 seconds",
        "features": [
            "Document analysis and extraction",
            "Multi-turn conversational AI",
            "Web search integration",
            "Intelligent synthesis and insights",
            "Multiple export formats",
            "Interactive visualizations",
            "Advanced reasoning techniques"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is operational",
        "timeout_limit": "120 seconds",
        "services": {
            "nltk": "available",
            "llm_integration": "ready",
            "document_processing": "ready",
            "search": "ready"
        }
    }

@app.get("/api/info")
def api_info():
    """Provide API information and available endpoints"""
    return {
        "api_version": "1.0.0",
        "timeout_limit": "120 seconds",
        "endpoints": {
            "upload": "/api/v1/upload - Document upload and processing",
            "chat": "/api/v1/chat - Conversational interface",
            "search": "/api/v1/search - Web search capabilities",
            "export": "/api/v1/export - Export research findings",
            "visualize": "/api/v1/visualize - Generate visualizations",
            "tools": "/api/v1/tools - Access research tools",
            "insights": "/api/v1/insights - Generate insights",
            "context": "/api/v1/context - Manage conversation context"
        },
        "supported_formats": {
            "input": ["PDF", "DOCX", "TXT", "MD"],
            "output": ["JSON", "PDF", "DOCX", "HTML", "CSV"]
        }
    }