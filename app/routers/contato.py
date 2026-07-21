import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MensagemContato
from app.templating import templates
from app.utils.cpf import apenas_digitos

router = APIRouter()

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOTIVOS_VALIDOS = {"Reclamação", "Suporte", "Sugestão"}


class ContatoRequest(BaseModel):
    motivo: str
    nome: str
    email: str
    telefone: str
    mensagem: str


@router.get("/contato")
def tela_contato(request: Request):
    return templates.TemplateResponse(request, "contato.html", {})


@router.post("/api/contato")
def enviar_contato(body: ContatoRequest, db: Session = Depends(get_db)):
    nome = body.nome.strip()
    email = body.email.strip().lower()
    telefone = apenas_digitos(body.telefone)
    mensagem = body.mensagem.strip()

    if body.motivo not in MOTIVOS_VALIDOS:
        return JSONResponse({"message": "Selecione o motivo do contato."}, status_code=400)
    if len(nome) < 2:
        return JSONResponse({"message": "Informe seu nome."}, status_code=400)
    if not EMAIL_REGEX.match(email):
        return JSONResponse({"message": "Informe um e-mail válido."}, status_code=400)
    if len(telefone) < 10:
        return JSONResponse(
            {"message": "Informe telefone ou celular com DDD (mínimo 10 dígitos)."}, status_code=400
        )
    if len(mensagem) < 5:
        return JSONResponse({"message": "Escreva sua mensagem (mínimo 5 caracteres)."}, status_code=400)

    db.add(
        MensagemContato(
            motivo=body.motivo, nome=nome, email=email, telefone=telefone, mensagem=mensagem
        )
    )
    db.commit()

    # Envio automático de e-mail ainda não configurado (sem SMTP definido) —
    # a mensagem fica registrada no banco para atendimento manual por ora.
    return {
        "message": "Mensagem recebida! Nossa equipe vai te responder em breve por e-mail.",
        "emailSent": False,
    }
