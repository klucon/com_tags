from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Tag(Base):
    __tablename__ = "com_tags_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(20), default="#6c757d")
    status: Mapped[str] = mapped_column(String(20), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class TagAssignment(Base):
    __tablename__ = "com_tags_assignments"
    __table_args__ = (
        UniqueConstraint("context", "item_id", "tag_id", name="uq_com_tags_context_item_tag"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    context: Mapped[str] = mapped_column(String(100), index=True)
    item_id: Mapped[int] = mapped_column(Integer, index=True)
    tag_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
