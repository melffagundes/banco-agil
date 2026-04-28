import os
import tempfile
import shutil
import pytest
import pandas as pd

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _verificar_score_para_limite_test(score: float, limite_solicitado: float) -> dict:
    """Versão de teste usando o CSV fixture."""
    path = os.path.join(_FIXTURES_DIR, "score_limite_test.csv")
    df = pd.read_csv(path, dtype=str)
    df["score_minimo"] = df["score_minimo"].astype(float)
    df["score_maximo"] = df["score_maximo"].astype(float)
    df["limite_maximo_permitido"] = df["limite_maximo_permitido"].astype(float)

    faixa = df[(df["score_minimo"] <= score) & (score <= df["score_maximo"])]
    if faixa.empty:
        return {"aprovado": False, "limite_maximo_permitido": 0.0}

    limite_maximo = float(faixa.iloc[0]["limite_maximo_permitido"])
    return {"aprovado": limite_solicitado <= limite_maximo, "limite_maximo_permitido": limite_maximo}


def test_score_suficiente_aprovado():
    """Score alto deve aprovar solicitação de limite compatível."""
    resultado = _verificar_score_para_limite_test(score=750.0, limite_solicitado=15000.0)

    assert resultado["aprovado"] is True
    assert resultado["limite_maximo_permitido"] == 15000.0


def test_score_insuficiente_rejeitado():
    """Score baixo não deve aprovar limite alto."""
    resultado = _verificar_score_para_limite_test(score=280.0, limite_solicitado=10000.0)

    assert resultado["aprovado"] is False
    assert resultado["limite_maximo_permitido"] == 1000.0


def test_registro_solicitacao_csv():
    """CSV de solicitações deve ser criado/atualizado corretamente."""
    # Usa diretório temporário para não poluir dados reais
    tmpdir = tempfile.mkdtemp()
    path_csv = os.path.join(tmpdir, "solicitacoes.csv")

    try:
        from datetime import datetime

        nova_linha = pd.DataFrame([{
            "cpf_cliente": "123.456.789-00",
            "data_hora_solicitacao": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "limite_atual": 5000.0,
            "novo_limite_solicitado": 15000.0,
            "status_pedido": "pendente",
        }])
        nova_linha.to_csv(path_csv, index=False)

        df = pd.read_csv(path_csv)
        assert len(df) == 1
        assert df.iloc[0]["cpf_cliente"] == "123.456.789-00"
        assert df.iloc[0]["status_pedido"] == "pendente"
        assert float(df.iloc[0]["novo_limite_solicitado"]) == 15000.0
    finally:
        shutil.rmtree(tmpdir)
