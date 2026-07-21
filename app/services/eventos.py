"""Log de eventos do sistema, usado pela aba Operação da área administrativa.

Nomes de tipo usados hoje: login_sucesso, login_falha, cadastro,
consulta_criada, pix_criado, pix_pago.
"""

from sqlalchemy.orm import Session

from app.models import EventoSistema

TIPOS_LABEL = {
    "login_sucesso": "Login realizado",
    "login_falha": "Falha de login",
    "cadastro": "Novo cadastro",
    "consulta_criada": "Consulta realizada",
    "pix_criado": "Cobrança Pix criada",
    "pix_pago": "Pix pago",
}


def registrar_evento(
    db: Session,
    tipo: str,
    descricao: str | None = None,
    usuario_id: int | None = None,
    ip: str | None = None,
) -> None:
    db.add(EventoSistema(tipo=tipo, descricao=descricao, usuario_id=usuario_id, ip=ip))
    db.commit()
