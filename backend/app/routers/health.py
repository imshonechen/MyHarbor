from fastapi import APIRouter

from ..database import check_database_connection
from ..schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    try:
        check_database_connection()
        return HealthResponse(status="ok", database="ok")
    except Exception:
        return HealthResponse(status="degraded", database="error")

