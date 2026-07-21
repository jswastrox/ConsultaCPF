import math

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import usuario_logado
from app.database import get_db
from app.models import Consulta, Pedido
from app.templating import templates

router = APIRouter()

POR_PAGINA = 10


@router.get("/area-usuario")
def area_usuario(
    request: Request,
    pagina_consultas: int = 1,
    pagina_pagamentos: int = 1,
    db: Session = Depends(get_db),
):
    usuario = usuario_logado(request, db)
    if usuario is None:
        return RedirectResponse(url="/login", status_code=303)

    pagina_consultas = max(1, pagina_consultas)
    pagina_pagamentos = max(1, pagina_pagamentos)

    total_consultas = db.scalar(
        select(func.count()).select_from(Consulta).where(Consulta.usuario_id == usuario.id)
    )
    total_paginas_consultas = max(1, math.ceil(total_consultas / POR_PAGINA))
    pagina_consultas = min(pagina_consultas, total_paginas_consultas)
    consultas = db.scalars(
        select(Consulta)
        .where(Consulta.usuario_id == usuario.id)
        .order_by(Consulta.criado_em.desc())
        .limit(POR_PAGINA)
        .offset((pagina_consultas - 1) * POR_PAGINA)
    ).all()

    total_pagamentos = db.scalar(
        select(func.count())
        .select_from(Pedido)
        .where(Pedido.usuario_id == usuario.id, Pedido.status == "paid")
    )
    total_paginas_pagamentos = max(1, math.ceil(total_pagamentos / POR_PAGINA))
    pagina_pagamentos = min(pagina_pagamentos, total_paginas_pagamentos)
    compras = db.scalars(
        select(Pedido)
        .where(Pedido.usuario_id == usuario.id, Pedido.status == "paid")
        .order_by(Pedido.pago_em.desc())
        .limit(POR_PAGINA)
        .offset((pagina_pagamentos - 1) * POR_PAGINA)
    ).all()

    return templates.TemplateResponse(
        request,
        "area_usuario.html",
        {
            "usuario": usuario,
            "consultas": consultas,
            "compras": compras,
            "pagina_consultas": pagina_consultas,
            "total_paginas_consultas": total_paginas_consultas,
            "pagina_pagamentos": pagina_pagamentos,
            "total_paginas_pagamentos": total_paginas_pagamentos,
        },
    )
