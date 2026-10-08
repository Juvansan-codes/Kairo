from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router as api_router
from .models.api_schemas import HealthResponse

app = FastAPI(title="HNX26EPS06 - Floor Plan Reconstruction API")

# Development CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}
