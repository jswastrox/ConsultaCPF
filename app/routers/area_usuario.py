from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import usuario_logado
from app.database import get_db
from app.models import Consulta, Pedido
from app.templating import templates

router = APIRouter()


@router.get("/area-usuario")
def area_usuario(request: Request, db: Session = Depends(get_db)):
    usuario = usuario_logado(request, db)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=303)

    consultas = db.scalars(
        select(Consulta)
        .where(Consulta.usuario_id == usuario.id)
        .order_by(Consulta.criado_em.desc())
        .limit(50)
    ).all()

    compras = db.scalars(
        select(Pedido)
        .where(Pedido.usuario_id == usuario.id, Pedido.status == "paid")
        .order_by(Pedido.pago_em.desc())
        .limit(50)
    ).all()

    return templates.TemplateResponse(
        request,
        "area_usuario.html",
        {"usuario": usuario, "consultas": consultas, "compras": compras},
    )
