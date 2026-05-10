from __future__ import annotations

from html import escape
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.system_settings import get_runtime_settings
from src.core.templates import make_t

from .service import CONTEXT_ARTICLE, get_item_tag_ids, list_tags, set_item_tags_by_names


async def _component_t(db: AsyncSession):
    runtime = await get_runtime_settings(db)
    return make_t(runtime.locale, "com_tags")


async def render_article_tags_field(*, article: Any | None, db: AsyncSession, **_: object) -> str:
    ct = await _component_t(db)

    current_tags: list[Any] = []
    if article:
        tag_ids = await get_item_tag_ids(db, context=CONTEXT_ARTICLE, item_id=article.id)
        if tag_ids:
            all_tags = await list_tags(db)
            current_tags = [t for t in all_tags if t.id in tag_ids]

    chips_html = ""
    for tag in current_tags:
        t = escape(tag.title)
        chips_html += (
            f'<span class="cms-tag-chip">'
            f'<span class="cms-tag-chip-label">{t}</span>'
            f'<button type="button" class="cms-tag-chip-remove" aria-label="{escape(ct("com_tags.article.remove_aria", title=tag.title))}">&times;</button>'
            f'<input type="hidden" name="tag_names" value="{t}">'
            f'</span>'
        )

    placeholder = escape(ct("com_tags.article.input_placeholder"))
    hint = escape(ct("com_tags.article.input_hint"))
    label = escape(ct("com_tags.article.field.tags"))

    js = (
        "(function(){"
        "var wrap=document.getElementById('cmsTagWrap');"
        "var inp=document.getElementById('cmsTagInput');"
        "function addTag(val){"
        "val=val.trim();"
        "if(!val)return;"
        "var existing=wrap.querySelectorAll('input[name=\"tag_names\"]');"
        "for(var i=0;i<existing.length;i++){if(existing[i].value.toLowerCase()===val.toLowerCase())return;}"
        "var chip=document.createElement('span');"
        "chip.className='cms-tag-chip';"
        "var lbl=document.createElement('span');"
        "lbl.className='cms-tag-chip-label';"
        "lbl.textContent=val;"
        "var btn=document.createElement('button');"
        "btn.type='button';"
        "btn.className='cms-tag-chip-remove';"
        "btn.innerHTML='&times;';"
        "btn.setAttribute('aria-label','Odebrat '+val);"
        "btn.addEventListener('click',function(){chip.remove();});"
        "var hidden=document.createElement('input');"
        "hidden.type='hidden';"
        "hidden.name='tag_names';"
        "hidden.value=val;"
        "chip.appendChild(lbl);"
        "chip.appendChild(btn);"
        "chip.appendChild(hidden);"
        "wrap.insertBefore(chip,inp);"
        "}"
        "inp.addEventListener('keydown',function(e){"
        "if(e.key==='Enter'||e.key===','){e.preventDefault();addTag(inp.value);inp.value='';}"
        "if(e.key==='Backspace'&&inp.value===''&&wrap.querySelector('.cms-tag-chip')){"
        "wrap.querySelector('.cms-tag-chip:last-of-type').remove();}"
        "});"
        "wrap.querySelectorAll('.cms-tag-chip-remove').forEach(function(btn){"
        "btn.addEventListener('click',function(){btn.closest('.cms-tag-chip').remove();});"
        "});"
        "wrap.addEventListener('click',function(){inp.focus();});"
        "})();"
    )

    return (
        "<hr>"
        f'<div class="mb-3">'
        f'<div class="form-label fw-medium">{label}</div>'
        f'<div class="cms-tag-wrap" id="cmsTagWrap">'
        f"{chips_html}"
        f'<input type="text" class="cms-tag-input" id="cmsTagInput" placeholder="{placeholder}" autocomplete="off">'
        f"</div>"
        f'<div class="form-text">{hint}</div>'
        f"</div>"
        f"<script>{js}</script>"
    )


async def save_article_tags(*, article: Any, form: Any, db: AsyncSession, **_: object) -> None:
    raw = form.getlist("tag_names") if hasattr(form, "getlist") else []
    tag_names = [str(v).strip() for v in raw if str(v).strip()]
    await set_item_tags_by_names(db, context=CONTEXT_ARTICLE, item_id=article.id, tag_names=tag_names)
