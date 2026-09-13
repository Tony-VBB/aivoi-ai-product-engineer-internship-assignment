import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, Base, check_db_connection
from app.api.routes_complaints import router as complaints_router
from app.api.routes_ai import router as ai_router
from app.schemas.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aivoa-backend")

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Attempt table creation on startup
    if engine is not None:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("PostgreSQL database tables verified/created successfully.")
        except Exception as e:
            logger.warning("Could not automatically create database tables on startup: %s", str(e))
    yield
    # Shutdown logic if any
    logger.info("Application shutting down.")


app = FastAPI(
    title="AIVOA Pharmaceutical Complaint Management API",
    description="AI-powered QMS customer complaint processing system using LangGraph and FastAPI.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - MUST explicitly allow http://localhost:5173, http://localhost:5174, etc.
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
for default_origin in ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]:
    if default_origin not in origins:
        origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoint - explicitly required
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Independent health check returning status, database connectivity, and Groq configuration."""
    db_ok = check_db_connection()
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api")
    groq_ok = bool(groq_key and len(groq_key) > 10)

    return HealthResponse(
        status="healthy" if db_ok and groq_ok else ("degraded" if (groq_ok or db_ok) else "unhealthy"),
        service="aivoa-complaint-management-backend",
        version="1.0.0",
        database_connected=db_ok,
        groq_configured=groq_ok
    )


# Include API routers
app.include_router(complaints_router)
app.include_router(ai_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"

    uvicorn.run("main:app", host=host, port=port, reload=True)
