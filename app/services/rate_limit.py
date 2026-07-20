from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Consulta

settings = get_settings()


def excedeu_limite_consultas(db: Session, ip: str | None) -> bool:
    """Protege a consulta gratuita contra scraping em massa: limita quantas
    consultas um mesmo IP pode fazer em uma janela curta de tempo."""
    if not ip:
        return False

    desde = datetime.utcnow() - timedelta(minutes=settings.rate_limit_janela_minutos)
    total = db.scalar(
        select(func.count())
        .select_from(Consulta)
        .where(Consulta.ip == ip, Consulta.criado_em >= desde)
    )
    return total >= settings.rate_limit_consultas_por_janela
