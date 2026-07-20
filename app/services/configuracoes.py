from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Configuracao

PADROES = {
    "atendimento_whatsapp": "",
    "atendimento_email": "",
    "marketing_looker_studio_url": "",
    "financeiro_pix_taxa_percentual": "0.99",
    "financeiro_pix_taxa_fixa_centavos": "0",
    "financeiro_mostrar_pacote_teste": "false",
    "alertas_email": "",
    "alertas_whatsapp": "",
    "alertas_telegram_chat_id": "",
    "ads_google_customer_id": "",
    "ads_ga4_property_id": "",
}


def obter_configuracoes(db: Session, prefixo: str | None = None) -> dict[str, str]:
    valores = dict(PADROES)
    linhas = db.scalars(select(Configuracao)).all()
    for linha in linhas:
        valores[linha.chave] = linha.valor or ""
    if prefixo:
        return {k: v for k, v in valores.items() if k.startswith(prefixo)}
    return valores


def salvar_configuracoes(db: Session, valores: dict[str, str]) -> None:
    for chave, valor in valores.items():
        config = db.get(Configuracao, chave)
        if config is None:
            config = Configuracao(chave=chave, valor=valor)
            db.add(config)
        else:
            config.valor = valor
    db.commit()
