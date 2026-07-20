from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.services.busca_service import TIPOS_CONSULTA, TIPOS_META, buscar_candidatos
from app.templating import templates
from app.utils.cpf import apenas_digitos

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

    if tipo_limpo == "cpf":
        cpf_limpo = apenas_digitos(valor)
        return RedirectResponse(url=f"/cpf/{cpf_limpo}", status_code=303)

    resultado = buscar_candidatos(tipo_limpo, valor=valor, cep=cep, numero=numero)
    return templates.TemplateResponse(
        request,
        "busca_resultados.html",
        {"busca": resultado},
    )


@router.get("/sobre")
def sobre(request: Request):
    return templates.TemplateResponse(request, "sobre.html", {})
