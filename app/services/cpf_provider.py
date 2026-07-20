"""Camada de acesso a dados de CPF.

Diferente de CNPJ, não existe uma API pública gratuita e legal para consulta
de dados pessoais associados a um CPF — essa é uma base de dados restrita
(o próprio usuário do projeto vai configurar uma fonte própria no futuro,
ver `CPF_PROVIDER`/`CPF_PROVIDER_BASE_URL`/`CPF_PROVIDER_API_KEY`).

Até lá, `MockCPFProvider` gera dados FICTÍCIOS e determinísticos (mesma
entrada sempre produz a mesma "pessoa" fake) só para permitir desenvolver e
demonstrar o funil de prévia/pagamento/resultado sem depender de uma fonte
de dados reais de terceiros. `templates.env.globals["modo_demonstracao"]`
fica `True` enquanto `cpf_provider == "mock"`, e a UI deve deixar isso
visível para o usuário final.
"""

import hashlib
import random
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from app.utils.cpf import apenas_digitos

settings = get_settings()


class CPFNaoEncontrado(Exception):
    pass


class CPFProviderIndisponivel(Exception):
    pass


class CPFProvider(ABC):
    @abstractmethod
    def buscar(self, cpf: str) -> dict[str, Any]:
        """Retorna os dados brutos do CPF na fonte externa."""
        raise NotImplementedError


_PRIMEIROS_NOMES = [
    "João", "Maria", "José", "Ana", "Pedro", "Paula", "Carlos", "Fernanda",
    "Lucas", "Juliana", "Marcos", "Camila", "Rafael", "Beatriz", "Bruno",
    "Larissa", "Gabriel", "Patrícia", "Felipe", "Aline",
]
_SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
    "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
    "Almeida", "Barbosa",
]
_CIDADES_UF = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
    ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
    ("Recife", "PE"), ("Fortaleza", "CE"), ("Brasília", "DF"), ("Goiânia", "GO"),
]
_LOGRADOUROS = ["Rua das Flores", "Avenida Brasil", "Rua XV de Novembro", "Rua São João", "Alameda Santos"]
_SITUACOES = ["Regular", "Regular", "Regular", "Pendente de Regularização"]


class MockCPFProvider(CPFProvider):
    """Gera uma pessoa fictícia determinística a partir do CPF informado.
    Não representa nenhuma pessoa real — apenas para demonstração/dev."""

    def buscar(self, cpf: str) -> dict[str, Any]:
        cpf_limpo = apenas_digitos(cpf)
        seed = int(hashlib.sha256(cpf_limpo.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        primeiro = rng.choice(_PRIMEIROS_NOMES)
        sobrenomes = rng.sample(_SOBRENOMES, k=2)
        nome_completo = f"{primeiro} {sobrenomes[0]} {sobrenomes[1]}"

        nome_mae = f"{rng.choice(_PRIMEIROS_NOMES)} {rng.choice(_SOBRENOMES)} {rng.choice(_SOBRENOMES)}"

        ano_nascimento = rng.randint(1955, 2005)
        mes = rng.randint(1, 12)
        dia = rng.randint(1, 28)
        idade = date.today().year - ano_nascimento

        cidade, uf = rng.choice(_CIDADES_UF)
        ddd = rng.choice(["11", "21", "31", "41", "51", "61", "71", "81", "85"])
        telefone = f"{ddd}9{rng.randint(1000, 9999)}{rng.randint(1000, 9999)}"

        dominio = rng.choice(["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br"])
        email = f"{primeiro.lower()}.{sobrenomes[0].lower()}{rng.randint(1, 99)}@{dominio}"

        return {
            "nome_completo": nome_completo,
            "data_nascimento": f"{ano_nascimento:04d}-{mes:02d}-{dia:02d}",
            "idade": idade,
            "sexo": rng.choice(["Feminino", "Masculino"]),
            "nome_mae": nome_mae,
            "situacao_cadastral": rng.choice(_SITUACOES),
            "telefones": [telefone],
            "emails": [email],
            "endereco_logradouro": rng.choice(_LOGRADOUROS),
            "endereco_numero": str(rng.randint(10, 2500)),
            "endereco_complemento": None,
            "endereco_bairro": "Centro",
            "endereco_cep": f"{rng.randint(10000, 99999)}-{rng.randint(100, 999)}",
            "endereco_municipio": cidade,
            "endereco_uf": uf,
            "_mock": True,
        }


class HttpCPFProvider(CPFProvider):
    """Adapter genérico para uma futura API real de dados de CPF (a ser
    configurada pelo usuário). Espera um endpoint `GET {base_url}/{cpf}`
    autenticado por `Authorization: Bearer {api_key}` retornando JSON já no
    formato normalizado (mesmas chaves do `MockCPFProvider.buscar`)."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 15.0):
        self.base_url = (base_url or settings.cpf_provider_base_url).rstrip("/")
        self.api_key = api_key or settings.cpf_provider_api_key
        self.timeout = timeout

    def buscar(self, cpf: str) -> dict[str, Any]:
        cpf_limpo = apenas_digitos(cpf)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            resposta = httpx.get(f"{self.base_url}/{cpf_limpo}", headers=headers, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise CPFProviderIndisponivel(str(exc)) from exc

        if resposta.status_code == 404:
            raise CPFNaoEncontrado(cpf_limpo)
        if resposta.status_code >= 400:
            raise CPFProviderIndisponivel(f"Provedor retornou status {resposta.status_code}")
        return resposta.json()


_PROVIDERS: dict[str, type[CPFProvider]] = {
    "mock": MockCPFProvider,
    "http": HttpCPFProvider,
}


def get_provider() -> CPFProvider:
    classe = _PROVIDERS.get(settings.cpf_provider, MockCPFProvider)
    return classe()


def normalizar_pessoa(dados: dict[str, Any]) -> dict[str, Any]:
    """Formato já normalizado tanto pelo mock quanto pelo adapter HTTP —
    aqui só garantimos as chaves default e guardamos o payload bruto."""
    return {
        "nome_completo": dados.get("nome_completo"),
        "data_nascimento": dados.get("data_nascimento"),
        "idade": dados.get("idade"),
        "sexo": dados.get("sexo"),
        "nome_mae": dados.get("nome_mae"),
        "situacao_cadastral": dados.get("situacao_cadastral"),
        "telefones": dados.get("telefones") or [],
        "emails": dados.get("emails") or [],
        "endereco_logradouro": dados.get("endereco_logradouro"),
        "endereco_numero": dados.get("endereco_numero"),
        "endereco_complemento": dados.get("endereco_complemento"),
        "endereco_bairro": dados.get("endereco_bairro"),
        "endereco_cep": dados.get("endereco_cep"),
        "endereco_municipio": dados.get("endereco_municipio"),
        "endereco_uf": dados.get("endereco_uf"),
        "raw_json": dados,
        "fonte": settings.cpf_provider,
    }
