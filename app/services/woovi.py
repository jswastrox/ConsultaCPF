"""Integração com a Woovi (OpenPix) para cobranças Pix.

Docs: https://developers.woovi.com/
Autenticação: header "Authorization" com o AppID (não usa "Bearer").
"""

from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


class WooviError(Exception):
    pass


def _headers() -> dict[str, str]:
    return {
        "Authorization": settings.woovi_app_id,
        "Content-Type": "application/json",
    }


def criar_cobranca_pix(
    correlation_id: str, valor_centavos: int, comentario: str
) -> dict[str, Any]:
    """Cria uma cobrança Pix e retorna o payload da Woovi com QR code e copia-e-cola."""
    url = f"{settings.woovi_base_url}/api/v1/charge"
    payload = {
        "correlationID": correlation_id,
        "value": valor_centavos,
        "comment": comentario,
    }
    try:
        resposta = httpx.post(url, json=payload, headers=_headers(), timeout=15.0)
    except httpx.HTTPError as exc:
        raise WooviError(str(exc)) from exc

    if resposta.status_code >= 400:
        raise WooviError(f"Woovi retornou {resposta.status_code}: {resposta.text}")

    return resposta.json().get("charge", {})


def consultar_cobranca(correlation_id: str) -> dict[str, Any]:
    """Consulta o status atual de uma cobrança direto na Woovi (fonte da verdade).

    Usado tanto no polling do frontend quanto para validar o conteúdo de um
    webhook recebido antes de marcar um pedido como pago.
    """
    url = f"{settings.woovi_base_url}/api/v1/charge/{correlation_id}"
    try:
        resposta = httpx.get(url, headers=_headers(), timeout=15.0)
    except httpx.HTTPError as exc:
        raise WooviError(str(exc)) from exc

    if resposta.status_code >= 400:
        raise WooviError(f"Woovi retornou {resposta.status_code}: {resposta.text}")

    return resposta.json().get("charge", {})


def cobranca_esta_paga(charge: dict[str, Any]) -> bool:
    return (charge or {}).get("status") == "COMPLETED"
