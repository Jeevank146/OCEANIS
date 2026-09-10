import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import test_database_connection
from ingestion.worker import BackgroundIngestionWorker
from api.v1.system import router as system_router
from api.v1.ingestion import router as ingestion_router
from api.v1.data_sources import router as data_sources_router
from api.v1.weather import router as weather_router
from api.v1.marine import router as marine_router
from api.v1.earth_observation import router as earth_observation_router
from api.v1.geospatial import router as geospatial_router
from api.v1.disaster import router as disaster_router
from api.v1.marine_operations import router as operations_router
from api.v1.fishing import router as fishing_router
from api.v1.agents import router as agents_router
from api.v1.agents.disaster_safety import router as disaster_safety_agent_router
from api.v1.agents.earth_observation import router as earth_observation_agent_router
from api.v1.agents.geospatial_navigation import router as geospatial_navigation_agent_router
from api.v1.agents.marine_conditions import router as marine_conditions_agent_router
from api.v1.agents.marine_operations import router as marine_operations_agent_router
from api.v1.orchestrator import router as orchestrator_router
from api.v1.conversation import router as conversation_router
from api.v1.location import router as location_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup: start background ingestion worker if enabled
    worker = BackgroundIngestionWorker.get_instance()
    worker.start()
    yield
    # Application shutdown: gracefully cancel tasks
    await worker.stop()


app = FastAPI(
    title="OCEANIS API",
    description="Ocean Intelligence and Decision System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Configuration for Local Development and Public Cloud Production
default_origins = [
    "http://localhost:5173","http://localhost:5175",
    "http://127.0.0.1:5173","http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# Allow custom production frontend origins via FRONTEND_ORIGIN or ALLOWED_ORIGINS env vars
frontend_origin_env = os.getenv("FRONTEND_ORIGIN") or os.getenv("ALLOWED_ORIGINS")
if frontend_origin_env:
    for origin in frontend_origin_env.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned and cleaned not in default_origins:
            default_origins.append(cleaned)

# If wildcard is explicitly specified in ALLOWED_ORIGINS
if "*" in default_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(system_router, prefix="/api/v1")
app.include_router(location_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(data_sources_router, prefix="/api/v1")
app.include_router(weather_router, prefix="/api/v1")
app.include_router(marine_router, prefix="/api/v1")
app.include_router(earth_observation_router, prefix="/api/v1")
app.include_router(geospatial_router, prefix="/api/v1")
app.include_router(disaster_router, prefix="/api/v1")
app.include_router(operations_router, prefix="/api/v1")
app.include_router(fishing_router, prefix="/api/v1")
app.include_router(marine_conditions_agent_router, prefix="/api/v1")
app.include_router(earth_observation_agent_router, prefix="/api/v1")
app.include_router(geospatial_navigation_agent_router, prefix="/api/v1")
app.include_router(disaster_safety_agent_router, prefix="/api/v1")
app.include_router(marine_operations_agent_router, prefix="/api/v1")
app.include_router(orchestrator_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "project": "OCEANIS",
        "status": "online",
        "message": "Ocean Intelligence and Decision System API",
    }


@app.get("/health")
def health():
    try:
        postgis_version = test_database_connection()

        return {
            "status": "healthy",
            "database": "connected",
            "postgis": postgis_version,
        }

    except Exception as error:
        return {
            "status": "degraded",
            "database": "offline_or_initializing",
            "message": "API active with live upstream providers and cache fallback",
            "detail": str(error),
        }
