"""Helpers para formatacao numerica no padrao brasileiro."""


def fmt_brl(valor: float, casas: int = 2) -> str:
    """Formata número como moeda brasileira: 18000.5 -> 'R$ 18.000,50'."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "R$ 0,00"
    if v < 0:
        return "-" + fmt_brl(-v, casas)
    inteiro, _, dec = f"{v:,.{casas}f}".partition(".")
    inteiro = inteiro.replace(",", ".")
    return f"R$ {inteiro},{dec}" if dec else f"R$ {inteiro}"


def fmt_num(valor: float, casas: int = 2) -> str:
    """Formata número padrão BR: 18000.5 -> '18.000,50'."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "0,00"
    if v < 0:
        return "-" + fmt_num(-v, casas)
    inteiro, _, dec = f"{v:,.{casas}f}".partition(".")
    inteiro = inteiro.replace(",", ".")
    return f"{inteiro},{dec}" if dec else inteiro


def fmt_pct(valor: float, casas: int = 2, sinal: bool = False) -> str:
    """Formata percentual BR: 5.34 -> '5,34%' ou '+5,34%' se sinal=True."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "0,00%"
    prefixo = "+" if sinal and v > 0 else ""
    return f"{prefixo}{fmt_num(v, casas)}%"
