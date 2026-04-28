import os
import pytest

# Aponta para os fixtures de teste
_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _criar_auth_tool_com_fixture():
    """Cria uma versão da ferramenta de auth apontando para o CSV de teste."""
    import pandas as pd

    def autenticar_cliente_test(cpf: str, data_nascimento: str) -> dict:
        path = os.path.join(_FIXTURES_DIR, "clientes_test.csv")
        df = pd.read_csv(path, dtype=str)

        cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
        df["cpf_limpo"] = df["cpf"].str.replace(".", "").str.replace("-", "").str.strip()
        cliente = df[df["cpf_limpo"] == cpf_limpo]

        if cliente.empty:
            return {"autenticado": False, "erro": "CPF não encontrado."}

        cliente = cliente.iloc[0]
        if cliente["data_nascimento"].strip() != data_nascimento.strip():
            return {"autenticado": False, "erro": "Data de nascimento incorreta."}

        return {
            "autenticado": True,
            "nome": cliente["nome"],
            "score": float(cliente["score"]),
            "limite": float(cliente["limite_atual"]),
        }

    return autenticar_cliente_test


def test_autenticacao_valida():
    """CPF e data corretos devem retornar autenticado=True com dados do cliente."""
    autenticar = _criar_auth_tool_com_fixture()
    resultado = autenticar("123.456.789-00", "1990-05-15")

    assert resultado["autenticado"] is True
    assert resultado["nome"] == "João Silva"
    assert resultado["score"] == 750.0
    assert resultado["limite"] == 5000.0


def test_autenticacao_cpf_invalido():
    """CPF inexistente deve retornar autenticado=False."""
    autenticar = _criar_auth_tool_com_fixture()
    resultado = autenticar("000.000.000-00", "1990-05-15")

    assert resultado["autenticado"] is False
    assert "erro" in resultado


def test_autenticacao_data_invalida():
    """CPF correto mas data errada deve retornar autenticado=False."""
    autenticar = _criar_auth_tool_com_fixture()
    resultado = autenticar("123.456.789-00", "1991-01-01")

    assert resultado["autenticado"] is False
    assert "erro" in resultado
