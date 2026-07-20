"""Buscas multi-tipo para a página /consulta.

No modo demonstração, gera candidatos fictícios determinísticos a partir do
termo informado e reaproveita o MockCPFProvider (via CPF gerado) para o
detalhe. Com provedor HTTP real, esta camada pode ser trocada por lookups
reversos reais sem mudar a UI.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.cpf_provider import get_provider, normalizar_pessoa
from app.utils.cnpj import formatar_cnpj, validar_cnpj
from app.utils.cpf import (
    apenas_digitos,
    formatar_cpf,
    gerar_cpf_valido,
    mascarar_cpf,
    mascarar_email,
    mascarar_nome,
    mascarar_telefone,
)

TIPOS_CONSULTA = ("cpf", "telefone", "nome", "email", "endereco", "cnpj")

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
    "endereco": {
        "titulo": "Endereço",
        "descricao": "Consulte por CEP e número para obter uma lista de moradores.",
        "placeholder": "00000-000",
        "label": "CEP",
        "inputmode": "numeric",
        "maxlength": "9",
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


def _resultado_pessoa(cpf: str, termo_destaque: str | None = None) -> dict[str, Any]:
    provider = get_provider()
    dados = normalizar_pessoa(provider.buscar(cpf))
    return {
        "cpf": cpf,
        "cpf_formatado": formatar_cpf(cpf),
        "cpf_mascarado": mascarar_cpf(cpf),
        "nome_completo": dados.get("nome_completo") or "—",
        "nome_mascarado": mascarar_nome(dados.get("nome_completo") or ""),
        "situacao_cadastral": dados.get("situacao_cadastral") or "—",
        "municipio": dados.get("endereco_municipio") or "—",
        "uf": dados.get("endereco_uf") or "—",
        "telefone_mascarado": mascarar_telefone((dados.get("telefones") or [""])[0] if dados.get("telefones") else ""),
        "email_mascarado": mascarar_email((dados.get("emails") or [""])[0] if dados.get("emails") else ""),
        "termo_destaque": termo_destaque,
    }


def buscar_candidatos(
    tipo: str,
    valor: str = "",
    cep: str = "",
    numero: str = "",
) -> dict[str, Any]:
    tipo = (tipo or "cpf").strip().lower()
    if tipo not in TIPOS_CONSULTA:
        tipo = "cpf"

    meta = TIPOS_META[tipo]
    valor = (valor or "").strip()
    cep = (cep or "").strip()
    numero = (numero or "").strip()

    if tipo == "endereco":
        termo = f"{apenas_digitos(cep)}-{numero}"
        termo_exibido = f"CEP {cep}" + (f", nº {numero}" if numero else "")
    else:
        termo = valor
        termo_exibido = valor

    if not termo or (tipo == "endereco" and len(apenas_digitos(cep)) < 8):
        return {
            "tipo": tipo,
            "meta": meta,
            "termo": termo_exibido,
            "resultados": [],
            "empresa": None,
            "erro": "Informe um valor válido para continuar a busca.",
        }

    if tipo == "cnpj":
        cnpj = apenas_digitos(valor)
        if not validar_cnpj(cnpj):
            return {
                "tipo": tipo,
                "meta": meta,
                "termo": valor,
                "resultados": [],
                "empresa": None,
                "erro": "CNPJ inválido. Verifique os dígitos e tente novamente.",
            }
        seed = _seed(f"cnpj:{cnpj}")
        qtd_socios = 2 + (seed % 3)
        socios = [
            _resultado_pessoa(gerar_cpf_valido(seed + i * 9973), termo_destaque=formatar_cnpj(cnpj))
            for i in range(qtd_socios)
        ]
        razao = f"EMPRESA DEMO {_seed(cnpj) % 9000 + 1000} LTDA"
        return {
            "tipo": tipo,
            "meta": meta,
            "termo": formatar_cnpj(cnpj),
            "resultados": socios,
            "empresa": {
                "cnpj": formatar_cnpj(cnpj),
                "razao_social": razao,
                "situacao": "Ativa",
            },
            "erro": None,
        }

    seed_base = _seed(f"{tipo}:{termo.lower()}")
    qtd = 1 + (seed_base % 4)  # 1 a 4 resultados
    if tipo == "cpf":
        cpf = apenas_digitos(valor)
        resultados = [_resultado_pessoa(cpf)] if len(cpf) == 11 else []
    else:
        resultados = [
            _resultado_pessoa(
                gerar_cpf_valido(seed_base + i * 7919),
                termo_destaque=termo_exibido,
            )
            for i in range(qtd)
        ]

    return {
        "tipo": tipo,
        "meta": meta,
        "termo": termo_exibido,
        "resultados": resultados,
        "empresa": None,
        "erro": None if resultados else "Nenhum resultado encontrado para esta busca.",
    }
