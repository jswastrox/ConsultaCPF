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


_CAMPOS_POR_CATEGORIA = [
    ("Dados Pessoais", [
        ("👤", "Nome Completo", PACOTE_BASICO),
        ("📅", "Data de Nascimento", PACOTE_BASICO),
        ("🆔", "CPF", PACOTE_BASICO),
        ("🛡️", "Situação Cadastral", PACOTE_BASICO),
        ("👥", "Nome da Mãe", PACOTE_BASICO),
        ("📞", "Telefones", PACOTE_BASICO),
        ("✉️", "E-mails", PACOTE_BASICO),
        ("📍", "Endereços", PACOTE_BASICO),
    ]),
    ("Dados Complementares", [
        ("💍", "Estado Civil", PACOTE_COMPLETA),
        ("🪪", "RG", PACOTE_COMPLETA),
        ("💼", "Profissão", PACOTE_COMPLETA),
        ("💰", "Salário Estimado", PACOTE_COMPLETA),
        ("🏛️", "Pessoa Politicamente Exposta", PACOTE_COMPLETA),
    ]),
    ("Informações Adicionais", [
        ("⚰️", "Óbito", PACOTE_DETALHADA),
        ("🧓", "Aposentado(a)", PACOTE_DETALHADA),
        ("🏢", "Locais de Trabalho", PACOTE_DETALHADA),
        ("🏭", "Empresas e Sociedades", PACOTE_DETALHADA),
        ("🚗", "Veículos", PACOTE_DETALHADA),
        ("👪", "Parentes", PACOTE_DETALHADA),
        ("🎁", "Benefícios que Recebe", PACOTE_DETALHADA),
    ]),
]


def tabela_comparativa() -> list[dict]:
    """Monta a matriz usada na página de escolha de pacote: para cada campo,
    se ele está incluído no básico/completa/detalhada (cumulativo)."""
    grupos = []
    for categoria, campos in _CAMPOS_POR_CATEGORIA:
        linhas = []
        for icone, label, nivel_minimo in campos:
            linhas.append(
                {
                    "icone": icone,
                    "label": label,
                    "basico": nivel(nivel_minimo) <= nivel(PACOTE_BASICO),
                    "completa": nivel(nivel_minimo) <= nivel(PACOTE_COMPLETA),
                    "detalhada": nivel(nivel_minimo) <= nivel(PACOTE_DETALHADA),
                }
            )
        grupos.append({"categoria": categoria, "campos": linhas})
    return grupos
