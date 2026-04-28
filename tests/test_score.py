import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.score_calculator import calcular_score


def test_calculo_score_formal_sem_dividas():
    """Cenário favorável: emprego formal, boa renda, sem dívidas."""
    score = calcular_score(
        renda_mensal=5000.0,
        despesas_fixas=1500.0,
        tipo_emprego="formal",
        num_dependentes=1,
        tem_dividas="não",
    )
    assert score > 400
    assert 0 <= score <= 1000


def test_calculo_score_desempregado_com_dividas():
    """Cenário desfavorável: desempregado, sem renda, com dívidas."""
    score = calcular_score(
        renda_mensal=0.0,
        despesas_fixas=2000.0,
        tipo_emprego="desempregado",
        num_dependentes=3,
        tem_dividas="sim",
    )
    assert score < 100
    assert 0 <= score <= 1000


def test_score_clamped_entre_0_e_1000():
    """Score deve ser sempre limitado ao intervalo [0, 1000]."""
    score_alto = calcular_score(
        renda_mensal=100000.0,
        despesas_fixas=100.0,
        tipo_emprego="formal",
        num_dependentes=0,
        tem_dividas="não",
    )
    assert score_alto <= 1000

    score_baixo = calcular_score(
        renda_mensal=0.0,
        despesas_fixas=10000.0,
        tipo_emprego="desempregado",
        num_dependentes=5,
        tem_dividas="sim",
    )
    assert score_baixo >= 0


def test_calculo_score_autonomo():
    """Autônomo com renda média deve ter score intermediário."""
    score = calcular_score(
        renda_mensal=3000.0,
        despesas_fixas=1000.0,
        tipo_emprego="autônomo",
        num_dependentes=2,
        tem_dividas="não",
    )
    assert 0 <= score <= 1000
    assert score > 200
