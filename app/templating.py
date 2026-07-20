from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.auth import usuario_logado
from app.config import get_settings
from app.database import SessionLocal
from app.utils.cpf import (
    formatar_cpf,
    mascarar_cpf,
    mascarar_email,
    mascarar_nome,
    mascarar_telefone,
)

settings = get_settings()


def _contexto_usuario(request: Request) -> dict:
    """Disponibiliza `usuario_logado` em todo template, sem precisar repetir
    a consulta em cada rota (só o header já usa isso em toda página)."""
    db = SessionLocal()
    try:
        return {"usuario_logado": usuario_logado(request, db)}
    finally:
        db.close()


def _contexto_seo(request: Request) -> dict:
    """URL canônica da página atual, usada em <link rel=canonical> e og:url."""
    return {"canonical_url": f"{settings.site_url.rstrip('/')}{request.url.path}"}


templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent / "templates",
    context_processors=[_contexto_usuario, _contexto_seo],
)
templates.env.filters["cpf"] = formatar_cpf
templates.env.filters["mascarar_nome"] = mascarar_nome
templates.env.filters["mascarar_cpf"] = mascarar_cpf
templates.env.filters["mascarar_telefone"] = mascarar_telefone
templates.env.filters["mascarar_email"] = mascarar_email
templates.env.globals["site_name"] = settings.site_name
templates.env.globals["site_url"] = settings.site_url.rstrip("/")
templates.env.globals["report_price"] = settings.report_price_cents / 100
templates.env.globals["contact_email"] = settings.contact_email
templates.env.globals["modo_demonstracao"] = settings.cpf_provider == "mock"
