import random
import re


def apenas_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def formatar_cpf(cpf: str) -> str:
    d = apenas_digitos(cpf)
    if len(d) != 11:
        return cpf
    return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def _digito_verificador(base: str) -> str:
    peso = len(base) + 1
    soma = sum(int(d) * p for d, p in zip(base, range(peso, 1, -1)))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def validar_cpf(cpf: str) -> bool:
    d = apenas_digitos(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    dv1 = _digito_verificador(d[:9])
    dv2 = _digito_verificador(d[:9] + dv1)
    return d[-2:] == dv1 + dv2


def gerar_cpf_valido(seed: int) -> str:
    """Gera um CPF sintaticamente válido e determinístico a partir de uma seed.

    Usado só no modo demonstração para buscas reversas (telefone, nome, etc.)
    produzirem candidatos estáveis que reaproveitam o fluxo de `/cpf/{cpf}`.
    """
    rng = random.Random(seed)
    base = "".join(str(rng.randint(0, 9)) for _ in range(9))
    while len(set(base)) == 1:
        base = "".join(str(rng.randint(0, 9)) for _ in range(9))
    dv1 = _digito_verificador(base)
    dv2 = _digito_verificador(base + dv1)
    return base + dv1 + dv2


def mascarar_nome(nome: str) -> str:
    """Mantém o primeiro nome visível e mascara as demais partes — usado na
    prévia gratuita, antes do desbloqueio pago."""
    partes = (nome or "").split()
    if not partes:
        return nome
    mascaradas = [partes[0]]
    for p in partes[1:]:
        mascaradas.append(p[0] + "*" * (len(p) - 1) if len(p) > 1 else p)
    return " ".join(mascaradas)


def mascarar_cpf(cpf: str) -> str:
    d = apenas_digitos(cpf)
    if len(d) != 11:
        return cpf
    return f"{d[0:3]}.***.***-{d[9:11]}"


def mascarar_telefone(telefone: str) -> str:
    d = apenas_digitos(telefone)
    if len(d) < 10:
        return "(**) *****-****"
    ddd, ultimos = d[0:2], d[-2:]
    return f"({ddd}) *****-**{ultimos}"


def mascarar_email(email: str) -> str:
    if not email or "@" not in email:
        return "****"
    usuario, dominio = email.split("@", 1)
    if len(usuario) <= 2:
        visivel = usuario[0] + "*"
    else:
        visivel = usuario[0] + "*" * (len(usuario) - 2) + usuario[-1]
    return f"{visivel}@{dominio}"
