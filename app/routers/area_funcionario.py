from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import usuario_logado
from app.database import get_db
from app.models import PAPEL_ADMIN, PAPEL_FUNCIONARIO, Pedido, Usuario
from app.templating import templates

router = APIRouter()


@router.get("/area-funcionario")
def area_funcionario(request: Request, q: str = "", db: Session = Depends(get_db)):
    usuario = usuario_logado(request, db)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=303)
    if not usuario.is_funcionario:
        return RedirectResponse(url="/", status_code=303)

    clientes_query = select(Usuario).where(
        Usuario.papel.not_in([PAPEL_ADMIN, PAPEL_FUNCIONARIO])
    )
    if q:
        termo = f"%{q}%"
        clientes_query = clientes_query.where(
            or_(Usuario.nome.ilike(termo), Usuario.email.ilike(termo), Usuario.telefone.ilike(termo))
        )
    clientes = db.scalars(clientes_query.order_by(Usuario.criado_em.desc()).limit(100)).all()

    total_clientes = db.scalar(
        select(func.count()).select_from(Usuario).where(
            Usuario.papel.not_in([PAPEL_ADMIN, PAPEL_FUNCIONARIO])
        )
    )
    novos_30_dias = db.scalar(
        select(func.count()).select_from(Usuario).where(
            Usuario.papel.not_in([PAPEL_ADMIN, PAPEL_FUNCIONARIO]),
            Usuario.criado_em >= datetime.utcnow() - timedelta(days=30),
        )
    )

    consultas_por_cliente = {}
    if clientes:
        contagem = db.execute(
            select(Pedido.usuario_id, func.count())
            .where(Pedido.usuario_id.in_([c.id for c in clientes]), Pedido.status == "paid")
            .group_by(Pedido.usuario_id)
        ).all()
        consultas_por_cliente = {usuario_id: total for usuario_id, total in contagem}

    return templates.TemplateResponse(
        request,
        "area_funcionario.html",
        {
            "clientes": clientes,
            "total_clientes": total_clientes,
            "novos_30_dias": novos_30_dias,
            "consultas_por_cliente": consultas_por_cliente,
            "q": q,
        },
    )
