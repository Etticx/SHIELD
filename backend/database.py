# =============================================================================
# SHIELD — Database layer
#
# Uses SQLAlchemy 2.x async engine with asyncpg driver.
# Table: evaluations — one row per /predict call.
#
# Startup sequence (called from main.py lifespan):
#   await init_db()   — creates tables if they don't exist (idempotent)
#
# Per-request usage:
#   async with get_session() as session:
#       session.add(record)
#       await session.commit()
#
# If DATABASE_URL is not set the DB layer silently disables itself and
# every DB operation becomes a no-op — the prediction endpoint still works.
# =============================================================================

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import String, Float, DateTime, Text, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger("shield.db")

# ---------------------------------------------------------------------------
# Engine — created lazily in init_db(), None if DATABASE_URL is absent
# ---------------------------------------------------------------------------
_engine: object | None = None
_SessionLocal: async_sessionmaker | None = None  # type: ignore[type-arg]


# ---------------------------------------------------------------------------
# ORM base + model
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class Evaluation(Base):
    """One row per SME evaluation submitted via POST /predict."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Identification metadata ──────────────────────────────────────────────
    company_name:  Mapped[str]   = mapped_column(String(255), nullable=False)
    ssm_number:    Mapped[str]   = mapped_column(String(100), nullable=False)
    loan_amount:   Mapped[float] = mapped_column(Float,       nullable=False)
    evaluator:     Mapped[str]   = mapped_column(String(100), nullable=False)

    # ── Timestamp ────────────────────────────────────────────────────────────
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Model output ─────────────────────────────────────────────────────────
    probability_default:  Mapped[float] = mapped_column(Float,       nullable=False)
    risk_classification:  Mapped[str]   = mapped_column(String(50),  nullable=False)

    # ── JSON blobs (stored as TEXT for maximum portability) ──────────────────
    financial_inputs: Mapped[str] = mapped_column(Text, nullable=False)   # JSON dict
    shap_breakdown:   Mapped[str] = mapped_column(Text, nullable=False)   # JSON list
    advisory_report:  Mapped[str] = mapped_column(Text, nullable=False)   # plain text

    # ── Convenience serialiser ───────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "company_name":         self.company_name,
            "ssm_number":           self.ssm_number,
            "loan_amount":          self.loan_amount,
            "evaluator":            self.evaluator,
            "evaluated_at":         self.evaluated_at.isoformat(),
            "probability_default":  self.probability_default,
            "risk_classification":  self.risk_classification,
            "financial_inputs":     json.loads(self.financial_inputs),
            "shap_breakdown":       json.loads(self.shap_breakdown),
            "advisory_report":      self.advisory_report,
        }


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------

async def init_db(database_url: str | None) -> None:
    """
    Create the async engine and ensure all tables exist.
    Safe to call multiple times (CREATE TABLE IF NOT EXISTS semantics).
    If database_url is None or empty the function returns immediately —
    the application runs without persistence.
    """
    global _engine, _SessionLocal

    if not database_url:
        logger.warning(
            "DATABASE_URL not set — audit persistence disabled. "
            "Evaluations will NOT be saved."
        )
        return

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    _SessionLocal = async_sessionmaker(
        bind=_engine,            # type: ignore[arg-type]
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with _engine.begin() as conn:  # type: ignore[union-attr]
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database ready — evaluations table confirmed.")


async def close_db() -> None:
    """Dispose the connection pool on shutdown."""
    if _engine is not None:
        await _engine.dispose()  # type: ignore[union-attr]
        logger.info("Database connection pool closed.")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession | None, None]:
    """
    Async context manager that yields a session, or None if the DB is
    disabled.  Callers must guard: `if session is not None`.
    """
    if _SessionLocal is None:
        yield None
        return

    async with _SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
