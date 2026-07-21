"""Pacotes de desbloqueio do relatório de CPF (básico/completa/detalhada).

Cada pacote é cumulativo: "completa" inclui tudo do "básico" + campos extras,
"detalhada" inclui tudo do "completa" + campos extras. O preço de cada Pedido
é sempre o valor total do pacote escolhido (não um "delta" sobre o anterior).
"""

from app.config import get_settings
from app.models import ORDEM_PACOTES, PACOTE_BASICO, PACOTE_COMPLETA, PACOTE_DETALHADA

settings = get_settings()


def preco_centavos(pacote: str) -> int:
    return {
        PACOTE_BASICO: settings.report_price_cents,
        PACOTE_COMPLETA: settings.report_price_completa_cents,
        PACOTE_DETALHADA: settings.report_price_detalhada_cents,
    }.get(pacote, settings.report_price_cents)


def pacote_valido(pacote: str) -> str:
    return pacote if pacote in ORDEM_PACOTES else PACOTE_BASICO


def nivel(pacote: str) -> int:
    return ORDEM_PACOTES.index(pacote_valido(pacote))


def atinge(pacote_desbloqueado: str | None, pacote_necessario: str) -> bool:
    """O pacote efetivamente pago cobre o pacote exigido por um campo?"""
    if pacote_desbloqueado is None:
        return False
    return nivel(pacote_desbloqueado) >= nivel(pacote_necessario)


def maior_pacote(pacotes: list[str]) -> str | None:
    if not pacotes:
        return None
    return max(pacotes, key=nivel)
