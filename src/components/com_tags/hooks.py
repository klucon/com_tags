from __future__ import annotations

from html import escape
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.system_settings import get_runtime_settings
from src.core.templates import make_t

from .service import CONTEXT_ARTICLE, get_item_tag_ids, list_tags, set_item_tags


async def _component_t(db: AsyncSession):
    runtime = await get_runtime_settings(db)
    return make_t(runtime.locale, "com_tags")


async def render_article_tags_field(*, article: Any | None, db: AsyncSession, **_: object) -> str:
    ct = await _component_t(db)
    tags = await list_tags(db, published_only=True)
    current_ids = await get_item_tag_ids(db, context=CONTEXT_ARTICLE, item_id=article.id) if article else set()
    checkboxes = []
    for tag in tags:
        checked = " checked" if tag.id in current_ids else ""
        checkboxes.append(
            '<label class="form-check">'
            f'<input class="form-check-input" type="checkbox" name="tag_ids" value="{tag.id}" '
            f'form="cms-content-form"{checked}>'
            f'<span class="form-check-label">{escape(tag.title)}</span>'
            "</label>"
        )
    content = "".join(checkboxes) if checkboxes else f'<div class="text-body-secondary small">{escape(ct("com_tags.article.empty"))}</div>'
    return (
        '<hr>'
        f'<div class="mb-3"><div class="form-label fw-medium">{escape(ct("com_tags.article.field.tags"))}</div>'
        f'<div class="d-grid gap-1">{content}</div></div>'
    )


async def save_article_tags(*, article: Any, form: Any, db: AsyncSession, **_: object) -> None:
    raw_values = form.getlist("tag_ids") if hasattr(form, "getlist") else []
    tag_ids = {int(value) for value in raw_values if str(value).isdigit() and int(value) > 0}
    await set_item_tags(db, context=CONTEXT_ARTICLE, item_id=article.id, tag_ids=tag_ids)
