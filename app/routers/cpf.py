from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi.responses import RedirectResponse

from app.auth import usuario_logado
from app.database import get_db
from app.models import PACOTE_DETALHADA, Consulta, Pedido, Pessoa, Usuario
from app.services.cpf_provider import CPFNaoEncontrado, CPFProviderIndisponivel
from app.services.pacotes import atinge, maior_pacote, nivel as nivel_pacote, preco_centavos, tabela_comparativa
from app.services.pessoa_service import obter_pessoa
from app.services.rate_limit import excedeu_limite_consultas
from app.templating import templates
from app.utils.cpf import apenas_digitos, validar_cpf

router = APIRouter()

INTERVALO_MINIMO_ATUALIZACAO = timedelta(minutes=5)


def _pacote_desbloqueado_atual(db: Session, usuario: Usuario | None, cpf_limpo: str) -> str | None:
    """Maior pacote já pago pela CONTA logada para este CPF (a compra exige
    login, então é a conta — não um cookie de navegador — que carrega o
    "já paguei por isso"; funciona em qualquer dispositivo). "Detalhada" de
    graça se for conta de equipe (admin/funcionário)."""
    if usuario is None:
        return None
    if usuario.is_staff:
        return PACOTE_DETALHADA

    pedidos_pagos = db.scalars(
        select(Pedido).where(
            Pedido.usuario_id == usuario.id,
            Pedido.cpf == cpf_limpo,
            Pedido.status == "paid",
        )
    ).all()
    return maior_pacote([p.pacote for p in pedidos_pagos])


@router.get("/cpf/{cpf}")
def detalhe_cpf(
    cpf: str,
    request: Request,
    origem: str = "cpf",
    db: Session = Depends(get_db),
):
    cpf_limpo = apenas_digitos(cpf)
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

    # Uma nova consulta ao mesmo CPF pela mesma conta substitui a anterior no
    # histórico (atualiza a data) em vez de criar uma linha duplicada.
    consulta_existente = (
        db.scalar(
            select(Consulta).where(
                Consulta.usuario_id == usuario.id, Consulta.cpf == cpf_limpo
            )
        )
        if usuario is not None
        else None
    )
    if consulta_existente is not None:
        consulta_existente.ip = ip
        consulta_existente.user_agent = request.headers.get("user-agent")
        consulta_existente.criado_em = datetime.utcnow()
    else:
        db.add(
            Consulta(
                cpf=cpf_limpo,
                ip=ip,
                user_agent=request.headers.get("user-agent"),
                usuario_id=usuario.id if usuario else None,
            )
        )
    db.commit()

    pacote_desbloqueado = _pacote_desbloqueado_atual(db, usuario, cpf_limpo)
    desbloqueado = pacote_desbloqueado is not None
    nivel_completa = atinge(pacote_desbloqueado, "completa")
    nivel_detalhada = atinge(pacote_desbloqueado, "detalhada")

    # Se a busca foi feita pelo próprio CPF, mostrar o CPF completo na prévia
    # não vaza nada novo (o usuário já digitou esse CPF). Se a busca foi por
    # telefone/nome/e-mail/CNPJ, o CPF também fica mascarado até o pagamento.
    mostrar_cpf_completo = desbloqueado or origem == "cpf"

    # Mesma lógica para o nome: se a busca foi pelo nome completo, a pessoa
    # já digitou esse nome — mostrar mascarado só esconderia o que ela
    # mesma informou.
    mostrar_nome_completo = desbloqueado or origem == "nome"

    return templates.TemplateResponse(
        request,
        "cpf_detalhe.html",
        {
            "pessoa": pessoa,
            "desbloqueado": desbloqueado,
            "nivel_completa": nivel_completa,
            "nivel_detalhada": nivel_detalhada,
            "mostrar_cpf_completo": mostrar_cpf_completo,
            "mostrar_nome_completo": mostrar_nome_completo,
            "preco_completa": preco_centavos("completa") / 100,
            "preco_detalhada": preco_centavos("detalhada") / 100,
            "origem": origem,
        },
    )


@router.get("/cpf/{cpf}/desbloquear")
def escolher_pacote(
    cpf: str,
    request: Request,
    origem: str = "cpf",
    db: Session = Depends(get_db),
):
    cpf_limpo = apenas_digitos(cpf)
    if len(cpf_limpo) != 11 or not validar_cpf(cpf_limpo):
        return templates.TemplateResponse(
            request, "cpf_invalido.html", {"cpf_digitado": cpf}, status_code=400
        )

    pessoa = db.get(Pessoa, cpf_limpo)
    if pessoa is None:
        # Precisa ter passado pela prévia antes (é lá que a pessoa é consultada/cacheada).
        return RedirectResponse(url=f"/cpf/{cpf_limpo}?origem={origem}", status_code=303)

    mostrar_cpf_completo = origem == "cpf"

    usuario = usuario_logado(request, db)
    pacote_atual = _pacote_desbloqueado_atual(db, usuario, cpf_limpo)
    nivel_atual = nivel_pacote(pacote_atual) if pacote_atual else -1

    return templates.TemplateResponse(
        request,
        "cpf_desbloquear.html",
        {
            "pessoa": pessoa,
            "mostrar_cpf_completo": mostrar_cpf_completo,
            "categorias": tabela_comparativa(),
            "pacote_atual": pacote_atual,
            "nivel_atual": nivel_atual,
            "preco_basico": preco_centavos("basico") / 100,
            "preco_completa": preco_centavos("completa") / 100,
            "preco_detalhada": preco_centavos("detalhada") / 100,
        },
    )
