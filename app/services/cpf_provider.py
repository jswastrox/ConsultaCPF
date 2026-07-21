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
_ESTADOS_CIVIS = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"]
_PROFISSOES = [
    "Analista Administrativo", "Vendedor(a)", "Motorista", "Professor(a)",
    "Técnico(a) em Enfermagem", "Autônomo(a)", "Auxiliar de Produção",
    "Comerciante", "Cozinheiro(a)", "Eletricista",
]
_EMPRESAS_FANTASIA = ["Comércio", "Serviços", "Distribuidora", "Tecnologia", "Transportes"]
_PARENTESCOS = ["Pai", "Mãe", "Irmão(ã)", "Cônjuge", "Filho(a)"]
_MODELOS_VEICULO = [
    ("Fiat", "Uno"), ("Volkswagen", "Gol"), ("Chevrolet", "Onix"),
    ("Hyundai", "HB20"), ("Honda", "CG 160"), ("Yamaha", "Fazer"),
]
_BENEFICIOS = ["Bolsa Família", "Auxílio Brasil", "BPC/LOAS", "Seguro-desemprego"]


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

        # Pacote "completa"
        estado_civil = rng.choice(_ESTADOS_CIVIS)
        rg = f"{rng.randint(10, 99)}.{rng.randint(100, 999)}.{rng.randint(100, 999)}-{rng.randint(0, 9)}"
        profissao = rng.choice(_PROFISSOES)
        salario_estimado = round(rng.uniform(1518, 12000), 2)
        exposta_politicamente = rng.random() < 0.05

        # Pacote "detalhada"
        obito = rng.random() < 0.03
        aposentado = idade >= 60 and rng.random() < 0.5
        locais_trabalho = [
            {"empresa": f"{rng.choice(_SOBRENOMES)} {rng.choice(_EMPRESAS_FANTASIA)} Ltda", "cargo": profissao}
        ]
        empresas_envolvidas = (
            [f"{rng.choice(_SOBRENOMES)} {rng.choice(_EMPRESAS_FANTASIA)} Ltda (Sócio)"]
            if rng.random() < 0.3
            else []
        )
        veiculos = (
            [f"{m} {mo} {rng.randint(2005, 2023)} — placa {''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}{rng.randint(1000, 9999)}"
             for m, mo in [rng.choice(_MODELOS_VEICULO)]]
            if rng.random() < 0.5
            else []
        )
        parentes = [
            {"nome": f"{rng.choice(_PRIMEIROS_NOMES)} {rng.choice(_SOBRENOMES)}", "parentesco": p}
            for p in rng.sample(_PARENTESCOS, k=rng.randint(1, 3))
        ]
        beneficios = [rng.choice(_BENEFICIOS)] if rng.random() < 0.15 else []

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
            "estado_civil": estado_civil,
            "rg": rg,
            "profissao": profissao,
            "salario_estimado": salario_estimado,
            "exposta_politicamente": exposta_politicamente,
            "obito": obito,
            "aposentado": aposentado,
            "locais_trabalho": locais_trabalho,
            "empresas_envolvidas": empresas_envolvidas,
            "veiculos": veiculos,
            "parentes": parentes,
            "beneficios": beneficios,
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
        "estado_civil": dados.get("estado_civil"),
        "rg": dados.get("rg"),
        "profissao": dados.get("profissao"),
        "salario_estimado": dados.get("salario_estimado"),
        "exposta_politicamente": dados.get("exposta_politicamente"),
        "obito": dados.get("obito"),
        "aposentado": dados.get("aposentado"),
        "locais_trabalho": dados.get("locais_trabalho") or [],
        "empresas_envolvidas": dados.get("empresas_envolvidas") or [],
        "veiculos": dados.get("veiculos") or [],
        "parentes": dados.get("parentes") or [],
        "beneficios": dados.get("beneficios") or [],
        "raw_json": dados,
        "fonte": settings.cpf_provider,
    }
