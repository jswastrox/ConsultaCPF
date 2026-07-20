import re

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    SESSION_COOKIE,
    criar_sessao,
    definir_cookie_sessao,
    encerrar_sessao,
    hash_senha,
    limpar_cookie_sessao,
    promover_se_admin,
    verificar_senha,
)
from app.database import get_db
from app.models import PAPEL_CLIENTE, Usuario
from app.templating import templates

router = APIRouter()

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.get("/login")
def tela_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login")
def enviar_login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    email: str = Form(...),
    senha: str = Form(...),
    manter_conectado: bool = Form(False),
):
    email_normalizado = email.strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email_normalizado))

    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"erro": "E-mail ou senha inválidos.", "email": email},
            status_code=401,
        )

    if not usuario.ativo:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"erro": "Esta conta está desativada.", "email": email},
            status_code=403,
        )

    promover_se_admin(usuario)
    db.commit()

    token = criar_sessao(db, usuario, manter_conectado)
    redirect = RedirectResponse(url="/", status_code=303)
    definir_cookie_sessao(redirect, token, manter_conectado)
    return redirect


@router.get("/cadastro")
def tela_cadastro(request: Request):
    return templates.TemplateResponse(request, "cadastro.html", {})


@router.post("/cadastro")
def enviar_cadastro(
    request: Request,
    db: Session = Depends(get_db),
    nome: str = Form(...),
    email: str = Form(...),
    confirmar_email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    aceite_termos: bool = Form(False),
):
    valores = {"nome": nome, "email": email}

    def erro(msg: str, status_code: int = 400):
        return templates.TemplateResponse(
            request, "cadastro.html", {"erro": msg, **valores}, status_code=status_code
        )

    nome = nome.strip()
    email_normalizado = email.strip().lower()
    confirmar_email_normalizado = confirmar_email.strip().lower()

    if not nome:
        return erro("Informe seu nome.")
    if not EMAIL_REGEX.match(email_normalizado):
        return erro("Informe um e-mail válido.")
    if email_normalizado != confirmar_email_normalizado:
        return erro("Os e-mails informados não coincidem.")
    if len(senha) < 6:
        return erro("A senha precisa ter pelo menos 6 caracteres.")
    if senha != confirmar_senha:
        return erro("As senhas informadas não coincidem.")
    if not aceite_termos:
        return erro("É preciso aceitar os Termos de Uso e a Política de Privacidade.")

    existente = db.scalar(select(Usuario).where(Usuario.email == email_normalizado))
    if existente is not None:
        return erro("Já existe uma conta cadastrada com este e-mail.")

    usuario = Usuario(
        nome=nome,
        email=email_normalizado,
        senha_hash=hash_senha(senha),
        papel=PAPEL_CLIENTE,
    )
    promover_se_admin(usuario)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = criar_sessao(db, usuario, manter_conectado=True)
    redirect = RedirectResponse(url="/", status_code=303)
    definir_cookie_sessao(redirect, token, manter_conectado=True)
    return redirect


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    encerrar_sessao(db, token)
    redirect = RedirectResponse(url="/", status_code=303)
    limpar_cookie_sessao(redirect)
    return redirect
