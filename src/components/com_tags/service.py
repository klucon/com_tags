from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Tag, TagAssignment

CONTEXT_ARTICLE = "com_content.article"
STATUS_PUBLISHED = "published"
STATUS_UNPUBLISHED = "unpublished"
VALID_STATUSES = {STATUS_PUBLISHED, STATUS_UNPUBLISHED}

_SLUG_INVALID_RE = re.compile(r"[^a-z0-9\s-]")
_SLUG_SEPARATOR_RE = re.compile(r"[\s_-]+")
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class TagError(ValueError):
    def __init__(self, key: str, **kwargs: object) -> None:
        super().__init__(key)
        self.key = key
        self.kwargs = kwargs


@dataclass(frozen=True)
class TagPayload:
    title: str
    slug: str
    description: str
    color: str
    status: str


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = _SLUG_INVALID_RE.sub("", ascii_text.lower().strip())
    return _SLUG_SEPARATOR_RE.sub("-", cleaned).strip("-")


def normalize_status(status: str | None) -> str:
    candidate = (status or STATUS_PUBLISHED).strip().lower()
    return candidate if candidate in VALID_STATUSES else STATUS_PUBLISHED


def normalize_color(color: str | None) -> str:
    candidate = (color or "").strip()
    return candidate if _COLOR_RE.match(candidate) else "#6c757d"


def build_payload(
    *,
    title: str,
    slug: str | None,
    description: str | None,
    color: str | None,
    status: str | None,
) -> TagPayload:
    clean_title = title.strip()
    if not clean_title:
        raise TagError("com_tags.error.title_required")

    clean_slug = slugify(slug or clean_title)
    if not clean_slug:
        raise TagError("com_tags.error.slug_required")

    return TagPayload(
        title=clean_title,
        slug=clean_slug,
        description=(description or "").strip(),
        color=normalize_color(color),
        status=normalize_status(status),
    )


async def list_tags(db: AsyncSession, *, published_only: bool = False) -> list[Tag]:
    query = select(Tag)
    if published_only:
        query = query.where(Tag.status == STATUS_PUBLISHED)
    query = query.order_by(Tag.title.asc(), Tag.id.asc())
    return (await db.execute(query)).scalars().all()


async def get_tag(db: AsyncSession, tag_id: int) -> Tag | None:
    return (await db.execute(select(Tag).where(Tag.id == tag_id))).scalar_one_or_none()


async def _slug_exists(db: AsyncSession, slug: str, *, exclude_id: int | None = None) -> bool:
    query = select(Tag).where(Tag.slug == slug)
    if exclude_id is not None:
        query = query.where(Tag.id != exclude_id)
    return (await db.execute(query)).scalar_one_or_none() is not None


async def create_tag(db: AsyncSession, payload: TagPayload) -> Tag:
    if await _slug_exists(db, payload.slug):
        raise TagError("com_tags.error.slug_exists", slug=payload.slug)
    tag = Tag(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        color=payload.color,
        status=payload.status,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag: Tag, payload: TagPayload) -> Tag:
    if await _slug_exists(db, payload.slug, exclude_id=tag.id):
        raise TagError("com_tags.error.slug_exists", slug=payload.slug)
    tag.title = payload.title
    tag.slug = payload.slug
    tag.description = payload.description
    tag.color = payload.color
    tag.status = payload.status
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag_id: int) -> None:
    await db.execute(delete(TagAssignment).where(TagAssignment.tag_id == tag_id))
    await db.execute(delete(Tag).where(Tag.id == tag_id))
    await db.commit()


async def get_item_tag_ids(db: AsyncSession, *, context: str, item_id: int) -> set[int]:
    rows = (
        await db.execute(
            select(TagAssignment.tag_id).where(
                TagAssignment.context == context,
                TagAssignment.item_id == item_id,
            )
        )
    ).scalars().all()
    return set(rows)


async def set_item_tags(db: AsyncSession, *, context: str, item_id: int, tag_ids: set[int]) -> None:
    existing = (
        await db.execute(
            select(TagAssignment).where(
                TagAssignment.context == context,
                TagAssignment.item_id == item_id,
            )
        )
    ).scalars().all()
    existing_ids = {item.tag_id for item in existing}

    for assignment in existing:
        if assignment.tag_id not in tag_ids:
            await db.delete(assignment)

    for tag_id in tag_ids - existing_ids:
        db.add(TagAssignment(context=context, item_id=item_id, tag_id=tag_id))

    await db.commit()


async def get_or_create_tag_by_name(db: AsyncSession, name: str) -> Tag | None:
    """Najde tag podle slugu nebo vytvoří nový publikovaný. Nedělá commit."""
    clean = name.strip()
    if not clean:
        return None
    slug = slugify(clean)
    if not slug:
        return None
    existing = (await db.execute(select(Tag).where(Tag.slug == slug))).scalar_one_or_none()
    if existing:
        return existing
    tag = Tag(title=clean, slug=slug, description="", color="#6c757d", status=STATUS_PUBLISHED)
    db.add(tag)
    await db.flush()
    return tag


async def set_item_tags_by_names(
    db: AsyncSession, *, context: str, item_id: int, tag_names: list[str]
) -> None:
    tag_ids: set[int] = set()
    for name in tag_names:
        tag = await get_or_create_tag_by_name(db, name)
        if tag and tag.id:
            tag_ids.add(tag.id)
    await set_item_tags(db, context=context, item_id=item_id, tag_ids=tag_ids)
