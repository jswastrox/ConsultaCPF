import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import usuario_logado
from app.config import get_settings
from app.database import get_db
from app.deps import get_or_create_buyer_token
from app.models import PACOTE_BASICO, Pessoa, Pedido
from app.services import woovi
from app.services.eventos import registrar_evento
from app.services.pacotes import pacote_valido, preco_centavos
from app.utils.cpf import apenas_digitos, formatar_cpf

router = APIRouter()
settings = get_settings()

_NOMES_PACOTE = {"basico": "Básico", "completa": "Completa", "detalhada": "Detalhada"}


class CriarPedidoRequest(BaseModel):
    cpf: str
    pacote: str = PACOTE_BASICO


@router.post("/api/pedidos")
def criar_pedido(
    body: CriarPedidoRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    usuario = usuario_logado(request, db)
    if usuario is None:
        raise HTTPException(401, "É necessário estar logado para comprar um relatório.")

    cpf_limpo = apenas_digitos(body.cpf)
    pessoa = db.get(Pessoa, cpf_limpo)
    if pessoa is None:
        raise HTTPException(404, "CPF não encontrado. Consulte antes de comprar o resultado completo.")

    pacote = pacote_valido(body.pacote)
    valor_centavos = preco_centavos(pacote)

    buyer_token = get_or_create_buyer_token(request, response)
    correlation_id = f"consultacpf-{uuid.uuid4().hex[:20]}"

    try:
        charge = woovi.criar_cobranca_pix(
            correlation_id=correlation_id,
            valor_centavos=valor_centavos,
            comentario=f"Relatorio {_NOMES_PACOTE[pacote]} - CPF {formatar_cpf(cpf_limpo)}",
        )
    except woovi.WooviError as exc:
        raise HTTPException(502, f"Não foi possível gerar a cobrança Pix: {exc}") from exc

    pedido = Pedido(
        correlation_id=correlation_id,
        cpf=cpf_limpo,
        buyer_token=buyer_token,
        usuario_id=usuario.id if usuario else None,
        valor_centavos=valor_centavos,
        status="pending",
        pacote=pacote,
        qrcode_image=charge.get("qrCodeImage"),
        brcode=charge.get("brCode"),
    )
    db.add(pedido)
    db.commit()
    registrar_evento(
        db, "pix_criado",
        descricao=f"Pacote {_NOMES_PACOTE[pacote]} - CPF {formatar_cpf(cpf_limpo)} - R$ {valor_centavos / 100:.2f}",
        usuario_id=usuario.id, ip=request.client.host if request.client else None,
    )

    return {
        "correlation_id": correlation_id,
        "qrcode_image": pedido.qrcode_image,
        "brcode": pedido.brcode,
        "valor_centavos": pedido.valor_centavos,
    }


@router.get("/api/pedidos/{correlation_id}/status")
def status_pedido(correlation_id: str, db: Session = Depends(get_db)):
    pedido = db.scalar(select(Pedido).where(Pedido.correlation_id == correlation_id))
    if pedido is None:
        raise HTTPException(404, "Pedido não encontrado.")

    if pedido.status == "pending":
        try:
            charge = woovi.consultar_cobranca(correlation_id)
            if woovi.cobranca_esta_paga(charge):
                pedido.status = "paid"
                pedido.pago_em = datetime.utcnow()
                db.commit()
                registrar_evento(
                    db, "pix_pago",
                    descricao=f"CPF {formatar_cpf(pedido.cpf)} - R$ {pedido.valor_centavos / 100:.2f}",
                    usuario_id=pedido.usuario_id,
                )
        except woovi.WooviError:
            pass  # mantém status atual; o webhook ainda pode confirmar depois

    return {"status": pedido.status, "cpf": pedido.cpf}


@router.post("/webhooks/woovi")
async def webhook_woovi(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    charge = payload.get("charge") or {}
    correlation_id = charge.get("correlationID")
    if not correlation_id:
        return {"ok": True}

    pedido = db.scalar(select(Pedido).where(Pedido.correlation_id == correlation_id))
    if pedido is None or pedido.status == "paid":
        return {"ok": True}

    # Não confiamos apenas no corpo do webhook: confirmamos direto na Woovi.
    try:
        charge_confirmado = woovi.consultar_cobranca(correlation_id)
    except woovi.WooviError:
        return {"ok": True}

    if woovi.cobranca_esta_paga(charge_confirmado):
        pedido.status = "paid"
        pedido.pago_em = datetime.utcnow()
        db.commit()
        registrar_evento(
            db, "pix_pago",
            descricao=f"CPF {formatar_cpf(pedido.cpf)} - R$ {pedido.valor_centavos / 100:.2f} (webhook)",
            usuario_id=pedido.usuario_id,
        )

    return {"ok": True}
