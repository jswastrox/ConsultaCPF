from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.utils.cpf import apenas_digitos

router = APIRouter()


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@router.post("/buscar")
def buscar(cpf: str = Form(...)):
    cpf_limpo = apenas_digitos(cpf)
    return RedirectResponse(url=f"/cpf/{cpf_limpo}", status_code=303)


@router.get("/sobre")
def sobre(request: Request):
    return templates.TemplateResponse(request, "sobre.html", {})
