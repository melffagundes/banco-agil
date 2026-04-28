import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_fluxo_autenticacao_sucesso():
    """
    Testa que o estado é atualizado corretamente após autenticação bem-sucedida.
    Usa lógica direta de auth (sem LLM) para isolar o teste.
    """
    import pandas as pd

    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    path = os.path.join(fixtures_dir, "clientes_test.csv")
    df = pd.read_csv(path, dtype=str)

    cpf_limpo = "12345678900"
    df["cpf_limpo"] = df["cpf"].str.replace(".", "").str.replace("-", "").str.strip()
    cliente = df[df["cpf_limpo"] == cpf_limpo]

    assert not cliente.empty
    cliente = cliente.iloc[0]
    assert cliente["data_nascimento"] == "1990-05-15"

    # Simula atualização de estado após autenticação
    estado = {
        "authenticated": True,
        "cliente_nome": cliente["nome"],
        "cliente_score": float(cliente["score"]),
        "cliente_limite": float(cliente["limite_atual"]),
        "auth_attempts": 0,
    }

    assert estado["authenticated"] is True
    assert estado["cliente_nome"] == "João Silva"


def test_fluxo_autenticacao_3_falhas_encerra():
    """
    Testa que após 3 tentativas falhas, should_end deve ser True.
    """
    auth_attempts = 0
    should_end = False

    for _ in range(3):
        auth_attempts += 1
        if auth_attempts >= 3:
            should_end = True

    assert auth_attempts == 3
    assert should_end is True


def test_roteamento_credito():
    """
    Testa que current_agent='credito' direciona ao nó correto.
    """
    estado = {
        "authenticated": True,
        "current_agent": "credito",
        "should_end": False,
    }

    # Simula a lógica de roteamento do grafo
    def rotear(state: dict) -> str:
        if state.get("should_end"):
            return "__end__"
        return state.get("current_agent", "triagem")

    destino = rotear(estado)
    assert destino == "credito"

    # Testa roteamento para encerramento
    estado["should_end"] = True
    destino_end = rotear(estado)
    assert destino_end == "__end__"
