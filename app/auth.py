"""Autenticação por sessão opaca (mesmo padrão do Consultar Motorista e do
ConsultaCNPJ), guardada em cookie httpOnly em vez de localStorage — mais
adequado a um app renderizado no servidor.
"""

import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PAPEL_ADMIN, Sessao, Usuario

settings = get_settings()

SESSION_COOKIE = "session_token"
DURACAO_SESSAO_CURTA = timedelta(hours=24)


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


def promover_se_admin(usuario: Usuario) -> None:
    """E-mail configurado em ADMIN_EMAIL é sempre promovido a admin (auto-seed)."""
    if settings.admin_email and usuario.email.lower() == settings.admin_email.lower():
        usuario.papel = PAPEL_ADMIN


def criar_sessao(db: Session, usuario: Usuario, manter_conectado: bool = True) -> str:
    token = secrets.token_hex(32)
    expira_em = None if manter_conectado else datetime.utcnow() + DURACAO_SESSAO_CURTA
    sessao = Sessao(
        usuario_id=usuario.id,
        token=token,
        manter_conectado=manter_conectado,
        expira_em=expira_em,
    )
    db.add(sessao)
    db.commit()
    return token


def definir_cookie_sessao(response: Response, token: str, manter_conectado: bool = True) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=None if manter_conectado else int(DURACAO_SESSAO_CURTA.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
    )


def limpar_cookie_sessao(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def obter_usuario_por_token(db: Session, token: str) -> Usuario | None:
    sessao = db.scalar(select(Sessao).where(Sessao.token == token))
    if sessao is None:
        return None
    if sessao.expira_em is not None and sessao.expira_em < datetime.utcnow():
        return None
    usuario = db.get(Usuario, sessao.usuario_id)
    if usuario is None or not usuario.ativo:
        return None
    return usuario


def usuario_logado(request: Request, db: Session) -> Usuario | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return obter_usuario_por_token(db, token)


def encerrar_sessao(db: Session, token: str | None) -> None:
    if not token:
        return
    sessao = db.scalar(select(Sessao).where(Sessao.token == token))
    if sessao is not None:
        db.delete(sessao)
        db.commit()
