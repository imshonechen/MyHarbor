from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Site(Base):
    __tablename__ = "site"
    __table_args__ = (
        CheckConstraint("status IN ('online', 'offline', 'unknown')", name="ck_site_status"),
        Index("ix_site_is_public_sort_order", "is_public", "sort_order"),
        Index("ix_site_tags", "tags"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    logo: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown", server_default=text("'unknown'"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=9999, server_default=text("9999"))
    last_check_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    status_logs: Mapped[list["SiteStatusLog"]] = relationship(
        back_populates="site", cascade="all, delete-orphan", passive_deletes=True
    )
    visit_logs: Mapped[list["VisitLog"]] = relationship(
        back_populates="site", cascade="all, delete-orphan", passive_deletes=True
    )
    visit_stats: Mapped[list["VisitStats"]] = relationship(
        back_populates="site", cascade="all, delete-orphan", passive_deletes=True
    )


class SiteConfig(Base):
    __tablename__ = "site_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class SiteStatusLog(Base):
    __tablename__ = "site_status_log"
    __table_args__ = (
        CheckConstraint("status IN ('online', 'offline')", name="ck_site_status_log_status"),
        Index("ix_site_status_log_site_id_checked_at", "site_id", "checked_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    response_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    site: Mapped["Site"] = relationship(back_populates="status_logs")


class VisitLog(Base):
    __tablename__ = "visit_log"
    __table_args__ = (Index("ix_visit_log_site_id_visited_at", "site_id", "visited_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("site.id", ondelete="CASCADE"), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    site: Mapped["Site"] = relationship(back_populates="visit_logs")


class VisitStats(Base):
    __tablename__ = "visit_stats"
    __table_args__ = (
        UniqueConstraint("site_id", "date", name="uq_visit_stats_site_id_date"),
        Index("ix_visit_stats_site_id_date", "site_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("site.id", ondelete="CASCADE"), nullable=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    site: Mapped["Site"] = relationship(back_populates="visit_stats")
