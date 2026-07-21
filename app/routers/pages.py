from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.services.busca_service import TIPOS_CONSULTA, TIPOS_META, resolver_cpf
from app.templating import templates

router = APIRouter()


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@router.get("/consulta")
@router.get("/consulta/{tipo}")
def consulta(request: Request, tipo: str | None = None):
    tipo_ativo = (tipo or "").strip().lower()
    if tipo_ativo and tipo_ativo not in TIPOS_CONSULTA:
        return RedirectResponse(url="/consulta", status_code=303)
    return templates.TemplateResponse(
        request,
        "consulta.html",
        {
            "tipos": TIPOS_META,
            "tipo_ativo": tipo_ativo or None,
            "tipos_ordem": TIPOS_CONSULTA,
        },
    )


@router.post("/buscar")
def buscar(
    request: Request,
    tipo: str = Form("cpf"),
    valor: str = Form(""),
    cep: str = Form(""),
    numero: str = Form(""),
):
    tipo_limpo = (tipo or "cpf").strip().lower()
    if tipo_limpo not in TIPOS_CONSULTA:
        tipo_limpo = "cpf"

    cpf_alvo = resolver_cpf(tipo_limpo, valor)
    if not cpf_alvo:
        return RedirectResponse(url=f"/consulta/{tipo_limpo}", status_code=303)

    # `origem` diz à tela de prévia se o CPF pode ser mostrado completo (a
    # pessoa já sabia o CPF, pois foi ela quem digitou) ou se deve continuar
    # mascarado (a busca foi por telefone/nome/e-mail/CNPJ, então o CPF em
    # si também é informação nova, paga).
    return RedirectResponse(url=f"/cpf/{cpf_alvo}?origem={tipo_limpo}", status_code=303)


@router.get("/sobre")
def sobre(request: Request):
    return templates.TemplateResponse(request, "sobre.html", {})
