from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from app.config import get_settings
from app.templating import templates

router = APIRouter()
settings = get_settings()


@router.get("/robots.txt")
def robots_txt():
    # Páginas individuais de CPF (/cpf/{cpf}) NUNCA devem ser indexadas —
    # ainda que os dados de prévia sejam mascarados, é dado pessoal de
    # terceiros e não uma entidade pública como um CNPJ.
    conteudo = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /cpf/\n"
        "Disallow: /area-usuario\n"
        "Disallow: /area-funcionario\n"
        "Disallow: /area-admin\n"
        f"Sitemap: {settings.site_url.rstrip('/')}/sitemap.xml\n"
    )
    return PlainTextResponse(conteudo)


@router.get("/sitemap.xml")
def sitemap_xml():
    # Só páginas estáticas/institucionais. Diferente do ConsultaCNPJ (onde
    # empresas são entidades públicas e viram páginas indexáveis), aqui as
    # páginas de resultado são sobre pessoas físicas e não entram no sitemap.
    base = settings.site_url.rstrip("/")
    paginas_estaticas = [
        ("/", "daily", "1.0"),
        ("/consulta", "daily", "0.9"),
        ("/sobre", "monthly", "0.5"),
        ("/termos", "yearly", "0.3"),
        ("/privacidade", "yearly", "0.3"),
    ]

    urls = [
        f"<url><loc>{base}{caminho}</loc><changefreq>{freq}</changefreq><priority>{prio}</priority></url>"
        for caminho, freq, prio in paginas_estaticas
    ]

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@router.get("/termos")
def termos(request: Request):
    return templates.TemplateResponse(request, "termos.html", {})


@router.get("/privacidade")
def privacidade(request: Request):
    return templates.TemplateResponse(request, "privacidade.html", {})
