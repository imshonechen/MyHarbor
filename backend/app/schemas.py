from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, field_serializer


class HealthResponse(BaseModel):
    status: str
    database: str


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any


class PublicConfigData(BaseModel):
    site_title: str
    site_description: str
    copyright: str
    icp_number: str


class PublicSiteItem(BaseModel):
    id: int
    name: str
    url: str
    logo: str | None
    description: str | None
    tags: str
    tags_list: list[str]
    is_public: bool
    status: str
    sort_order: int
    last_check_time: datetime | None

    @field_serializer('last_check_time')
    def serialize_last_check_time(self, dt: datetime | None, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class PublicSitesData(BaseModel):
    items: list[PublicSiteItem]
    total: int


class VisitRecordData(BaseModel):
    recorded: bool
