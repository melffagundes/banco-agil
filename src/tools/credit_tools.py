import os
from datetime import datetime
import pandas as pd
from langchain_core.tools import tool
from src.tools.csv_tools import ler_csv_seguro, escrever_csv_seguro

_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


@tool
def consultar_limite(cpf: str) -> dict:
    """Retorna o limite atual e score do cliente a partir do CPF."""
    path = os.path.join(_BASE_DIR, "clientes.csv")
    df = ler_csv_seguro(path)

    if df.empty:
        return {"erro": "Base de clientes indisponível no momento."}

    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    df["cpf_limpo"] = df["cpf"].str.replace(".", "").str.replace("-", "").str.strip()
    cliente = df[df["cpf_limpo"] == cpf_limpo]

    if cliente.empty:
        return {"erro": "Cliente não encontrado."}

    cliente = cliente.iloc[0]
    return {
        "nome": cliente["nome"],
        "score": float(cliente["score"]),
        "limite_atual": float(cliente["limite_atual"]),
    }


@tool
def verificar_score_para_limite(score: float, limite_solicitado: float) -> dict:
    """
    Verifica em score_limite.csv se o score do cliente permite o limite solicitado.
    Retorna: aprovado (bool) e limite_maximo_permitido (float).
    """
    path = os.path.join(_BASE_DIR, "score_limite.csv")
    df = ler_csv_seguro(path)

    if df.empty:
        return {"erro": "Tabela de score indisponível no momento."}

    df["score_minimo"] = df["score_minimo"].astype(float)
    df["score_maximo"] = df["score_maximo"].astype(float)
    df["limite_maximo_permitido"] = df["limite_maximo_permitido"].astype(float)

    faixa = df[(df["score_minimo"] <= score) & (score <= df["score_maximo"])]

    if faixa.empty:
        return {"aprovado": False, "limite_maximo_permitido": 0.0}

    limite_maximo = float(faixa.iloc[0]["limite_maximo_permitido"])
    aprovado = limite_solicitado <= limite_maximo

    return {"aprovado": aprovado, "limite_maximo_permitido": limite_maximo}


@tool
def registrar_solicitacao_aumento(cpf: str, limite_atual: float, novo_limite: float) -> dict:
    """
    Registra a solicitação de aumento de limite em solicitacoes_aumento_limite.csv.
    Retorna confirmação do registro.
    """
    path = os.path.join(_BASE_DIR, "solicitacoes_aumento_limite.csv")
    df = ler_csv_seguro(path)

    nova_linha = pd.DataFrame([{
        "cpf_cliente": cpf,
        "data_hora_solicitacao": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "limite_atual": limite_atual,
        "novo_limite_solicitado": novo_limite,
        "status_pedido": "pendente",
    }])

    if df.empty:
        df = nova_linha
    else:
        df = pd.concat([df, nova_linha], ignore_index=True)

    sucesso = escrever_csv_seguro(df, path)
    if sucesso:
        return {"registrado": True, "mensagem": "Solicitação registrada com sucesso."}
    return {"registrado": False, "mensagem": "Erro ao registrar solicitação."}


@tool
def atualizar_score_cliente(cpf: str, novo_score: float) -> bool:
    """Atualiza o score do cliente em clientes.csv. Retorna True se bem-sucedido."""
    path = os.path.join(_BASE_DIR, "clientes.csv")
    df = ler_csv_seguro(path)

    if df.empty:
        return False

    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    df["cpf_limpo"] = df["cpf"].str.replace(".", "").str.replace("-", "").str.strip()
    idx = df[df["cpf_limpo"] == cpf_limpo].index

    if idx.empty:
        return False

    # Garante score entre 0 e 1000
    novo_score_clamped = max(0, min(1000, round(novo_score)))
    df.loc[idx, "score"] = novo_score_clamped
    df = df.drop(columns=["cpf_limpo"])

    return escrever_csv_seguro(df, path)
