import os
from langchain_core.tools import tool
from src.tools.csv_tools import ler_csv_seguro

# Caminho base relativo à raiz do projeto banco_agil
_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


@tool
def autenticar_cliente(cpf: str, data_nascimento: str) -> dict:
    """
    Autentica o cliente verificando CPF e data de nascimento no arquivo de clientes.
    Retorna dict com: autenticado (bool), nome (str), score (float), limite (float).
    """
    path = os.path.join(_BASE_DIR, "clientes.csv")
    df = ler_csv_seguro(path)

    if df.empty:
        return {"autenticado": False, "erro": "Base de clientes indisponível no momento."}

    # Normaliza CPF removendo formatação para comparação
    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    df["cpf_limpo"] = df["cpf"].str.replace(".", "").str.replace("-", "").str.strip()

    cliente = df[df["cpf_limpo"] == cpf_limpo]

    if cliente.empty:
        return {"autenticado": False, "erro": "CPF não encontrado."}

    cliente = cliente.iloc[0]
    data_nasc_normalizada = data_nascimento.strip()

    if cliente["data_nascimento"].strip() != data_nasc_normalizada:
        return {"autenticado": False, "erro": "Data de nascimento incorreta."}

    return {
        "autenticado": True,
        "nome": cliente["nome"],
        "score": float(cliente["score"]),
        "limite": float(cliente["limite_atual"]),
    }
