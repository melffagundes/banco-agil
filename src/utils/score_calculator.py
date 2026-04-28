def calcular_score(
    renda_mensal: float,
    despesas_fixas: float,
    tipo_emprego: str,    # "formal" | "autônomo" | "desempregado"
    num_dependentes: int,
    tem_dividas: str      # "sim" | "não"
) -> float:
    """
    Calcula o score de crédito do cliente com base em dados financeiros.
    Retorna um valor entre 0 e 1000.

    Conforme especificação do desafio:
        peso_dividas = {"sim": -100, "não": 100}
        peso_dependentes = {0: 100, 1: 80, 2: 60, "3+": 30}
    """
    peso_renda = 30
    peso_emprego = {"formal": 300, "autônomo": 200, "desempregado": 0}
    peso_dependentes = {0: 100, 1: 80, 2: 60, "3+": 30}
    peso_dividas = {"sim": -100, "não": 100}

    dep_key = num_dependentes if num_dependentes <= 2 else "3+"

    # Normaliza entrada de dívidas (aceita bool ou string)
    if isinstance(tem_dividas, bool):
        divida_key = "sim" if tem_dividas else "não"
    else:
        divida_key = str(tem_dividas).strip().lower()
        # Aceita variações como "nao", "no", "yes", "s", "n"
        if divida_key in ("nao", "no", "false", "n", "0"):
            divida_key = "não"
        elif divida_key in ("yes", "s", "true", "1"):
            divida_key = "sim"

    score = (
        (renda_mensal / (despesas_fixas + 1)) * peso_renda
        + peso_emprego.get(tipo_emprego, 0)
        + peso_dependentes.get(dep_key, 30)
        + peso_dividas.get(divida_key, 0)
    )

    return max(0, min(1000, round(score)))
