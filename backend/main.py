# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from routes.upload import router as upload_router
from routes.chat import router as chat_router
from routes.search import router as search_router
from routes.export import router as export_router
from routes.visualize import router as visualize_router
from routes.tools import router as tools_router

# Create FastAPI app instance
app = FastAPI()

# Add CORS middleware to allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(export_router)
app.include_router(visualize_router)
app.include_router(tools_router)

# Root endpoint for health check
@app.get("/")
def root():
    return {"message": "API is running"}

