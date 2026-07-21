"""Resolução de buscas multi-tipo (CPF, telefone, nome, e-mail, CNPJ) para a
página /consulta.

Toda busca — não importa o dado usado para pesquisar — converge para a MESMA
tela de prévia (`/cpf/{cpf}`, mesmo padrão usado por outros sites do
segmento): resolvemos aqui qual CPF é o "resultado" da busca e a rota
`/buscar` apenas redireciona para lá. No modo demonstração, geramos um CPF
sintético determinístico a partir do termo pesquisado (`gerar_cpf_valido`),
reaproveitando o MockCPFProvider via esse CPF. Com um provedor HTTP real,
esta função pode passar a fazer um lookup reverso de verdade sem mudar a UI.
"""

from __future__ import annotations

import hashlib

from app.utils.cnpj import validar_cnpj
from app.utils.cpf import apenas_digitos, gerar_cpf_valido, validar_cpf

TIPOS_CONSULTA = ("cpf", "telefone", "nome", "email", "cnpj")

TIPOS_META = {
    "cpf": {
        "titulo": "Número do CPF",
        "descricao": "Consulte um CPF para obter as informações associadas ao titular.",
        "placeholder": "000.000.000-00",
        "label": "Digite o CPF",
        "inputmode": "numeric",
        "maxlength": "14",
    },
    "telefone": {
        "titulo": "Número do Telefone",
        "descricao": "Consulte um telefone para obter as informações do assinante da linha.",
        "placeholder": "(00) 00000-0000",
        "label": "Digite o telefone",
        "inputmode": "tel",
        "maxlength": "16",
    },
    "nome": {
        "titulo": "Nome Completo",
        "descricao": "Consulte pelo nome completo para encontrar pessoas associadas.",
        "placeholder": "Nome e sobrenome",
        "label": "Digite o nome completo",
        "inputmode": "text",
        "maxlength": "120",
    },
    "email": {
        "titulo": "E-mail",
        "descricao": "Consulte um e-mail para obter as informações associadas ao dono.",
        "placeholder": "nome@email.com",
        "label": "Digite o e-mail",
        "inputmode": "email",
        "maxlength": "120",
    },
    "cnpj": {
        "titulo": "Número do CNPJ",
        "descricao": "Consulte um CNPJ para obter informações associadas aos sócios.",
        "placeholder": "00.000.000/0000-00",
        "label": "Digite o CNPJ",
        "inputmode": "numeric",
        "maxlength": "18",
    },
}


def _seed(texto: str) -> int:
    return int(hashlib.sha256(texto.encode("utf-8")).hexdigest(), 16) % (2**32)


def resolver_cpf(tipo: str, valor: str = "", estado: str = "", cidade: str = "") -> str | None:
    """Retorna o CPF (11 dígitos) que a prévia deve exibir para essa busca,
    ou None se o valor informado for inválido."""
    tipo = (tipo or "cpf").strip().lower()
    valor = (valor or "").strip()
    if not valor:
        return None

    if tipo == "cpf":
        cpf = apenas_digitos(valor)
        return cpf if validar_cpf(cpf) else None

    if tipo == "cnpj":
        cnpj = apenas_digitos(valor)
        return gerar_cpf_valido(_seed(f"cnpj:{cnpj}")) if validar_cnpj(cnpj) else None

    if tipo == "nome":
        # Estado/cidade são opcionais, mas deixam a busca mais assertiva:
        # incluí-los no seed muda qual candidato é encontrado, simulando um
        # filtro geográfico real sobre um nome comum.
        estado = (estado or "").strip().lower()
        cidade = (cidade or "").strip().lower()
        return gerar_cpf_valido(_seed(f"nome:{valor.lower()}:{estado}:{cidade}"))

    # telefone, email: qualquer termo não vazio resolve a um único candidato
    # determinístico (mesmo termo -> sempre a mesma "pessoa").
    return gerar_cpf_valido(_seed(f"{tipo}:{valor.lower()}"))
