from fastapi import APIRouter
from database import test_database_connection

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health")
def system_health():
    try:
        postgis_version = test_database_connection()

        return {
            "status": "healthy",
            "database": "connected",
            "postgis": postgis_version,
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error),
        }