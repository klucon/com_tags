from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.admin.deps import CurrentAdminUser
from src.api.admin.render import admin_render
from src.core.system_settings import get_runtime_settings
from src.core.templates import make_t
from src.database.base import get_db_session

from .service import (
    TagError,
    build_payload,
    create_tag,
    delete_tag as delete_tag_record,
    get_tag,
    list_tags,
    update_tag,
)

router = APIRouter(prefix="/admin/com_tags", tags=["com_tags"])


async def _component_t(db: AsyncSession):
    runtime = await get_runtime_settings(db)
    return make_t(runtime.locale, "com_tags")


def _set_flash(request: Request, flash_type: str, text: str) -> None:
    request.session["flash"] = {"type": flash_type, "text": text}


@router.get("", response_class=HTMLResponse)
async def index(
    request: Request,
    user: CurrentAdminUser,
    db: AsyncSession = Depends(get_db_session),
) -> HTMLResponse:
    return await admin_render(
        "admin/com_tags/index.html",
        request=request,
        db=db,
        user=user,
        ct=await _component_t(db),
        tags=await list_tags(db),
        flash=request.session.pop("flash", None),
    )


@router.get("/new", response_class=HTMLResponse)
async def new_form(
    request: Request,
    user: CurrentAdminUser,
    db: AsyncSession = Depends(get_db_session),
) -> HTMLResponse:
    return await admin_render(
        "admin/com_tags/form.html",
        request=request,
        db=db,
        user=user,
        ct=await _component_t(db),
        tag=None,
        flash=request.session.pop("flash", None),
    )


@router.post("/new")
async def new_submit(
    request: Request,
    user: CurrentAdminUser,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    ct = await _component_t(db)
    form = await request.form()
    try:
        tag = await create_tag(db, _payload_from_form(form))
    except TagError as exc:
        _set_flash(request, "danger", ct(exc.key, **exc.kwargs))
        return RedirectResponse("/admin/com_tags/new", status_code=303)
    _set_flash(request, "success", ct("com_tags.success.created", title=tag.title))
    return RedirectResponse("/admin/com_tags", status_code=303)


@router.get("/{tag_id}/edit", response_class=HTMLResponse)
async def edit_form(
    tag_id: int,
    request: Request,
    user: CurrentAdminUser,
    db: AsyncSession = Depends(get_db_session),
) -> HTMLResponse | Response:
    tag = await get_tag(db, tag_id)
    if tag is None:
        return RedirectResponse("/admin/com_tags", status_code=303)
    return await admin_render(
        "admin/com_tags/form.html",
        request=request,
        db=db,
        user=user,
        ct=await _component_t(db),
        tag=tag,
        flash=request.session.pop("flash", None),
    )


@router.post("/{tag_id}/edit")
async def edit_submit(
    tag_id: int,
    request: Request,
    user: CurrentAdminUser,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    tag = await get_tag(db, tag_id)
    if tag is None:
        return RedirectResponse("/admin/com_tags", status_code=303)
    ct = await _component_t(db)
    form = await request.form()
    try:
        await update_tag(db, tag, _payload_from_form(form))
    except TagError as exc:
        _set_flash(request, "danger", ct(exc.key, **exc.kwargs))
        return RedirectResponse(f"/admin/com_tags/{tag_id}/edit", status_code=303)
    _set_flash(request, "success", ct("com_tags.success.updated"))
    return RedirectResponse("/admin/com_tags", status_code=303)


@router.post("/{tag_id}/delete")
async def delete_submit(
    tag_id: int,
    request: Request,
    user: CurrentAdminUser,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    await delete_tag_record(db, tag_id)
    ct = await _component_t(db)
    _set_flash(request, "success", ct("com_tags.success.deleted"))
    return RedirectResponse("/admin/com_tags", status_code=303)


def _payload_from_form(form: object):
    return build_payload(
        title=str(form.get("title", "")),
        slug=str(form.get("slug", "")),
        description=str(form.get("description", "")),
        color=str(form.get("color", "#6c757d")),
        status=str(form.get("status", "published")),
    )
