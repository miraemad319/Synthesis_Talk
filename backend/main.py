from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import nltk

try:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")

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
    description="Collaborative Research Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
   allow_origins=["http://localhost:5173"],  # ← your Vite/React origin
    allow_credentials=True,                    # must stay True so cookies flow
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (order doesn’t matter much; just needs to be included)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(export_router)
app.include_router(visualize_router)
app.include_router(tools_router)
app.include_router(insights_router)
app.include_router(context_router)

@app.get("/")
def root():
    return {"message": "SynthesisTalk API is running", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is operational"}


