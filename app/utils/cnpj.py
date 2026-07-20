from app.utils.cpf import apenas_digitos


def formatar_cnpj(cnpj: str) -> str:
    d = apenas_digitos(cnpj)
    if len(d) != 14:
        return cnpj
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _digito_verificador(base: str, pesos: list[int]) -> str:
    soma = sum(int(d) * p for d, p in zip(base, pesos))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def validar_cnpj(cnpj: str) -> bool:
    d = apenas_digitos(cnpj)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = _digito_verificador(d[:12], pesos1)
    dv2 = _digito_verificador(d[:12] + dv1, pesos2)
    return d[-2:] == dv1 + dv2
