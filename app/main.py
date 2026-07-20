from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import area_admin, area_funcionario, area_usuario, auth, cpf, pages, pagamentos, seo

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.site_name)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.ico")


app.include_router(pages.router)
app.include_router(seo.router)
app.include_router(auth.router)
app.include_router(cpf.router)
app.include_router(pagamentos.router)
app.include_router(area_usuario.router)
app.include_router(area_funcionario.router)
app.include_router(area_admin.router)
