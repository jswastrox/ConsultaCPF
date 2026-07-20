from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Pessoa
from app.services.cpf_provider import get_provider, normalizar_pessoa
from app.utils.cpf import apenas_digitos

settings = get_settings()


def obter_pessoa(db: Session, cpf: str, forcar_atualizacao: bool = False) -> Pessoa:
    """Busca a pessoa no cache local; se ausente ou expirada, consulta o provedor."""
    cpf_limpo = apenas_digitos(cpf)
    pessoa = db.get(Pessoa, cpf_limpo)

    cache_valido = (
        pessoa is not None
        and not forcar_atualizacao
        and pessoa.atualizado_em
        > datetime.utcnow() - timedelta(days=settings.cpf_cache_ttl_dias)
    )
    if cache_valido:
        return pessoa

    provider = get_provider()
    dados_brutos = provider.buscar(cpf_limpo)
    dados_pessoa = normalizar_pessoa(dados_brutos)

    if pessoa is None:
        pessoa = Pessoa(cpf=cpf_limpo, **dados_pessoa)
        db.add(pessoa)
    else:
        for campo, valor in dados_pessoa.items():
            setattr(pessoa, campo, valor)
        pessoa.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(pessoa)
    return pessoa
