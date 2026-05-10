"""Tag manager for KLUCON CMS content extensions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.registry import ComponentRegistry

_COMPONENT_DIR = Path(__file__).parent
_manifest: dict = {}


def _load_manifest() -> dict:
    global _manifest
    if not _manifest:
        try:
            _manifest = json.loads((_COMPONENT_DIR / "manifest.json").read_text(encoding="utf-8"))
        except Exception:
            _manifest = {}
    return _manifest


def setup(reg: "ComponentRegistry") -> None:
    from src.components.com_tags import admin, hooks as content_hooks
    from src.core.hooks import hooks
    from src.i18n.translator import translator

    manifest = _load_manifest()

    reg.register("com_tags", "src.components.com_tags")
    reg.register_display_name("com_tags", manifest.get("display_name_key", "extensions.name.com_tags"))
    reg.register_admin_url("com_tags", manifest.get("admin_url", "/admin/com_tags"))
    reg.register_router(admin.router)

    translator.load_domain("com_tags", _COMPONENT_DIR / "i18n")

    hooks.on("content.article.form.sidebar", content_hooks.render_article_tags_field)
    hooks.on("content.article.saved", content_hooks.save_article_tags)


async def uninstall_schema(engine: object) -> None:
    from src.components.com_tags.models import Tag, TagAssignment

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: TagAssignment.__table__.drop(sync_conn, checkfirst=True))
        await conn.run_sync(lambda sync_conn: Tag.__table__.drop(sync_conn, checkfirst=True))
