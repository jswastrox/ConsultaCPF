import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import usuario_logado
from app.config import get_settings
from app.database import get_db
from app.models import (
    ORDEM_PACOTES,
    PACOTE_BASICO,
    PACOTE_COMPLETA,
    PACOTE_DETALHADA,
    PAPEL_ADMIN,
    PAPEL_CLIENTE,
    PAPEL_FUNCIONARIO,
    Consulta,
    EventoSistema,
    Pedido,
    Usuario,
)
from app.services.configuracoes import obter_configuracoes, salvar_configuracoes
from app.services.eventos import TIPOS_LABEL
from app.templating import templates

router = APIRouter()
settings = get_settings()

PAPEIS_VALIDOS = {PAPEL_ADMIN, PAPEL_FUNCIONARIO, PAPEL_CLIENTE}
NOME_PACOTE = {PACOTE_BASICO: "Básico", PACOTE_COMPLETA: "Completo", PACOTE_DETALHADA: "Detalhado"}
POR_PAGINA = 10


def _exigir_admin(request: Request, db: Session):
    usuario = usuario_logado(request, db)
    if usuario is None:
        return None, RedirectResponse(url="/login", status_code=303)
    if not usuario.is_admin:
        return None, RedirectResponse(url="/", status_code=303)
    return usuario, None


def _periodo(inicio: str | None, fim: str | None) -> tuple[datetime, datetime]:
    fim_dt = datetime.strptime(fim, "%Y-%m-%d") + timedelta(days=1) if fim else datetime.utcnow()
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d") if inicio else fim_dt - timedelta(days=30)
    return inicio_dt, fim_dt


@router.get("/area-admin")
def area_admin(
    request: Request,
    aba: str = "financas",
    de: str | None = None,
    ate: str | None = None,
    email: str | None = None,
    pagina: int = 1,
    teste: str | None = None,
    db: Session = Depends(get_db),
):
    usuario, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect

    inicio_dt, fim_dt = _periodo(de, ate)
    pagina = max(1, pagina)
    contexto = {"aba": aba, "de": de, "ate": ate, "email": email or "", "teste": teste}

    if aba == "operacao":
        pedidos_query = select(Pedido).where(Pedido.criado_em >= inicio_dt, Pedido.criado_em < fim_dt)
        if email:
            pedidos_query = pedidos_query.join(Usuario, Pedido.usuario_id == Usuario.id).where(
                Usuario.email.ilike(f"%{email}%")
            )

        total_pedidos = db.scalar(
            select(func.count()).select_from(pedidos_query.subquery())
        )
        total_paginas = max(1, math.ceil(total_pedidos / POR_PAGINA))
        pagina = min(pagina, total_paginas)

        pedidos = db.scalars(
            pedidos_query.order_by(Pedido.criado_em.desc())
            .limit(POR_PAGINA)
            .offset((pagina - 1) * POR_PAGINA)
        ).all()

        criados = db.scalar(
            select(func.count()).select_from(Pedido).where(
                Pedido.criado_em >= inicio_dt, Pedido.criado_em < fim_dt
            )
        )
        pagos = db.scalar(
            select(func.count()).select_from(Pedido).where(
                Pedido.criado_em >= inicio_dt, Pedido.criado_em < fim_dt, Pedido.status == "paid"
            )
        )
        taxa_conversao = round((pagos / criados) * 100, 1) if criados else 0

        eventos = db.scalars(
            select(EventoSistema)
            .where(EventoSistema.criado_em >= inicio_dt, EventoSistema.criado_em < fim_dt)
            .order_by(EventoSistema.criado_em.desc())
            .limit(50)
        ).all()
        contagem_eventos_raw = db.execute(
            select(EventoSistema.tipo, func.count())
            .where(EventoSistema.criado_em >= inicio_dt, EventoSistema.criado_em < fim_dt)
            .group_by(EventoSistema.tipo)
        ).all()
        contagem_eventos = {tipo: total for tipo, total in contagem_eventos_raw}

        contexto.update(
            {
                "pedidos": pedidos,
                "criados": criados,
                "pagos": pagos,
                "taxa_conversao": taxa_conversao,
                "eventos": eventos,
                "tipos_label": TIPOS_LABEL,
                "contagem_eventos": contagem_eventos,
                "pagina": pagina,
                "total_paginas": total_paginas,
            }
        )

    elif aba == "alertas":
        contexto["config"] = obter_configuracoes(db, "alertas_")

    elif aba == "marketing":
        contexto["config"] = obter_configuracoes(db)

    elif aba == "configuracoes":
        contexto["config"] = obter_configuracoes(db)
        contexto["status_provedor"] = {
            "cpf_provider": settings.cpf_provider,
            "modo_demonstracao": settings.cpf_provider == "mock",
            "woovi_configurado": bool(settings.woovi_app_id),
        }

    elif aba == "usuarios":
        total_usuarios = db.scalar(select(func.count()).select_from(Usuario))
        novos_30_dias = db.scalar(
            select(func.count()).select_from(Usuario).where(
                Usuario.criado_em >= datetime.utcnow() - timedelta(days=30)
            )
        )

        usuarios_query = select(Usuario)
        if email:
            termo = f"%{email}%"
            usuarios_query = usuarios_query.where(
                or_(Usuario.nome.ilike(termo), Usuario.email.ilike(termo))
            )

        total_filtrados = db.scalar(select(func.count()).select_from(usuarios_query.subquery()))
        total_paginas = max(1, math.ceil(total_filtrados / POR_PAGINA))
        pagina = min(pagina, total_paginas)

        usuarios = db.scalars(
            usuarios_query.order_by(Usuario.criado_em.desc())
            .limit(POR_PAGINA)
            .offset((pagina - 1) * POR_PAGINA)
        ).all()

        consultas_pagas_por_usuario = {}
        if usuarios:
            contagem = db.execute(
                select(Pedido.usuario_id, func.count())
                .where(Pedido.usuario_id.in_([u.id for u in usuarios]), Pedido.status == "paid")
                .group_by(Pedido.usuario_id)
            ).all()
            consultas_pagas_por_usuario = {usuario_id: total for usuario_id, total in contagem}

        contexto.update(
            {
                "usuarios": usuarios,
                "consultas_pagas_por_usuario": consultas_pagas_por_usuario,
                "total_usuarios": total_usuarios,
                "novos_30_dias": novos_30_dias,
                "pagina": pagina,
                "total_paginas": total_paginas,
            }
        )

    else:  # financas (padrão)
        aba = "financas"
        contexto["aba"] = "financas"
        consultas_periodo = db.scalar(
            select(func.count()).select_from(Consulta).where(
                Consulta.criado_em >= inicio_dt, Consulta.criado_em < fim_dt
            )
        )
        pedidos_pagos = db.scalars(
            select(Pedido).where(
                Pedido.status == "paid", Pedido.pago_em >= inicio_dt, Pedido.pago_em < fim_dt
            )
        ).all()
        receita_bruta_centavos = sum(p.valor_centavos for p in pedidos_pagos)

        config_financeiro = obter_configuracoes(db, "financeiro_")
        taxa_percentual = float(config_financeiro.get("financeiro_pix_taxa_percentual") or 0)
        taxa_fixa_centavos = int(config_financeiro.get("financeiro_pix_taxa_fixa_centavos") or 0)
        custo_pix_centavos = int(
            receita_bruta_centavos * (taxa_percentual / 100) + len(pedidos_pagos) * taxa_fixa_centavos
        )
        receita_liquida_centavos = receita_bruta_centavos - custo_pix_centavos

        ticket_medio_centavos = (
            receita_bruta_centavos / len(pedidos_pagos) if pedidos_pagos else 0
        )

        breakdown_pacote = []
        for chave in ORDEM_PACOTES:
            pedidos_do_pacote = [p for p in pedidos_pagos if p.pacote == chave]
            breakdown_pacote.append(
                {
                    "pacote": NOME_PACOTE[chave],
                    "quantidade": len(pedidos_do_pacote),
                    "receita": sum(p.valor_centavos for p in pedidos_do_pacote) / 100,
                }
            )

        contexto.update(
            {
                "consultas_periodo": consultas_periodo,
                "resultados_vendidos": len(pedidos_pagos),
                "receita_bruta": receita_bruta_centavos / 100,
                "receita_liquida": receita_liquida_centavos / 100,
                "ticket_medio": ticket_medio_centavos / 100,
                "despesas": 0,
                "lucro": receita_liquida_centavos / 100,
                "breakdown_pacote": breakdown_pacote,
            }
        )

    return templates.TemplateResponse(request, "area_admin.html", contexto)


@router.post("/area-admin/configuracoes/atendimento")
def salvar_atendimento(
    request: Request,
    db: Session = Depends(get_db),
    whatsapp: str = Form(""),
    email: str = Form(""),
):
    _, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    salvar_configuracoes(
        db, {"atendimento_whatsapp": whatsapp.strip(), "atendimento_email": email.strip()}
    )
    return RedirectResponse(url="/area-admin?aba=configuracoes", status_code=303)


@router.post("/area-admin/configuracoes/marketing")
def salvar_marketing_config(
    request: Request,
    db: Session = Depends(get_db),
    looker_studio_url: str = Form(""),
):
    _, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    salvar_configuracoes(db, {"marketing_looker_studio_url": looker_studio_url.strip()})
    return RedirectResponse(url="/area-admin?aba=configuracoes", status_code=303)


@router.post("/area-admin/configuracoes/financeiro")
def salvar_financeiro(
    request: Request,
    db: Session = Depends(get_db),
    pix_taxa_percentual: str = Form("0"),
    pix_taxa_fixa_centavos: str = Form("0"),
    mostrar_pacote_teste: bool = Form(False),
):
    _, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    salvar_configuracoes(
        db,
        {
            "financeiro_pix_taxa_percentual": pix_taxa_percentual.strip() or "0",
            "financeiro_pix_taxa_fixa_centavos": pix_taxa_fixa_centavos.strip() or "0",
            "financeiro_mostrar_pacote_teste": "true" if mostrar_pacote_teste else "false",
        },
    )
    return RedirectResponse(url="/area-admin?aba=configuracoes", status_code=303)


@router.post("/area-admin/alertas")
def salvar_alertas(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(""),
    whatsapp: str = Form(""),
    telegram_chat_id: str = Form(""),
):
    _, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    salvar_configuracoes(
        db,
        {
            "alertas_email": email.strip(),
            "alertas_whatsapp": whatsapp.strip(),
            "alertas_telegram_chat_id": telegram_chat_id.strip(),
        },
    )
    return RedirectResponse(url="/area-admin?aba=alertas", status_code=303)


@router.post("/area-admin/alertas/teste")
def testar_alerta(request: Request, db: Session = Depends(get_db)):
    _, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    # Disparo real (e-mail/WhatsApp/Telegram) ainda não está implementado —
    # este endpoint só confirma que os canais configurados foram lidos, para
    # o admin verificar que salvou certo antes da integração existir.
    return RedirectResponse(url="/area-admin?aba=alertas&teste=1", status_code=303)


@router.post("/area-admin/marketing")
def salvar_marketing_ads(
    request: Request,
    db: Session = Depends(get_db),
    google_customer_id: str = Form(""),
    ga4_property_id: str = Form(""),
):
    _, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    salvar_configuracoes(
        db,
        {
            "ads_google_customer_id": google_customer_id.strip(),
            "ads_ga4_property_id": ga4_property_id.strip(),
        },
    )
    return RedirectResponse(url="/area-admin?aba=marketing", status_code=303)


@router.post("/area-admin/usuarios/{usuario_id}/papel")
def alterar_papel(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    papel: str = Form(...),
):
    admin, redirect = _exigir_admin(request, db)
    if redirect:
        return redirect
    if papel not in PAPEIS_VALIDOS:
        return RedirectResponse(url="/area-admin?aba=usuarios", status_code=303)

    alvo = db.get(Usuario, usuario_id)
    if alvo is not None and alvo.id != admin.id:
        alvo.papel = papel
        db.commit()

    return RedirectResponse(url="/area-admin?aba=usuarios", status_code=303)
