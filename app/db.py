from datetime import datetime

from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class ReleaseEvidenceRow(Base):
    __tablename__ = "release_evidence"

    release_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ReleaseApprovalRow(Base):
    __tablename__ = "release_approvals"

    release_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


def make_engine(database_url: str):
    return create_engine(database_url, future=True)


def make_session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False, future=True)
