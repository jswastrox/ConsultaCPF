from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import usuario_logado
from app.database import get_db
from app.deps import get_or_create_buyer_token
from app.models import Consulta, Pedido
from app.services.cpf_provider import CPFNaoEncontrado, CPFProviderIndisponivel
from app.services.pessoa_service import obter_pessoa
from app.services.rate_limit import excedeu_limite_consultas
from app.templating import templates
from app.utils.cpf import apenas_digitos, validar_cpf

router = APIRouter()

INTERVALO_MINIMO_ATUALIZACAO = timedelta(minutes=5)


@router.get("/cpf/{cpf}")
def detalhe_cpf(
    cpf: str,
    request: Request,
    response: Response,
    origem: str = "cpf",
    db: Session = Depends(get_db),
):
    cpf_limpo = apenas_digitos(cpf)
    buyer_token = get_or_create_buyer_token(request, response)
    usuario = usuario_logado(request, db)
    ip = request.client.host if request.client else None

    if len(cpf_limpo) != 11 or not validar_cpf(cpf_limpo):
        return templates.TemplateResponse(
            request,
            "cpf_invalido.html",
            {"cpf_digitado": cpf},
            status_code=400,
        )

    if excedeu_limite_consultas(db, ip):
        return templates.TemplateResponse(
            request, "limite_excedido.html", {}, status_code=429
        )

    try:
        pessoa = obter_pessoa(db, cpf_limpo)
    except CPFNaoEncontrado:
        return templates.TemplateResponse(
            request,
            "cpf_nao_encontrado.html",
            {"cpf": cpf_limpo},
            status_code=404,
        )
    except CPFProviderIndisponivel:
        return templates.TemplateResponse(
            request,
            "erro_provedor.html",
            {"cpf": cpf_limpo},
            status_code=502,
        )

    db.add(
        Consulta(
            cpf=cpf_limpo,
            ip=ip,
            user_agent=request.headers.get("user-agent"),
            usuario_id=usuario.id if usuario else None,
        )
    )
    db.commit()

    pedido_pago = db.scalar(
        select(Pedido).where(
            Pedido.buyer_token == buyer_token,
            Pedido.cpf == cpf_limpo,
            Pedido.status == "paid",
        )
    )

    # Equipe (admin/funcionário) tem acesso ao resultado completo sem pagar.
    desbloqueado = pedido_pago is not None or (usuario is not None and usuario.is_staff)

    # Se a busca foi feita pelo próprio CPF, mostrar o CPF completo na prévia
    # não vaza nada novo (o usuário já digitou esse CPF). Se a busca foi por
    # telefone/nome/e-mail/CNPJ, o CPF também fica mascarado até o pagamento.
    mostrar_cpf_completo = desbloqueado or origem == "cpf"

    return templates.TemplateResponse(
        request,
        "cpf_detalhe.html",
        {
            "pessoa": pessoa,
            "desbloqueado": desbloqueado,
            "mostrar_cpf_completo": mostrar_cpf_completo,
        },
    )
