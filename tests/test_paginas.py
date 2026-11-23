"""Todas as páginas executam sem erro e as interações principais funcionam (AppTest do Streamlit)."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from utils.config import PAGINA, RAIZ

TERESINA, PICOS = "221100", "220800"


def iniciar():
    return AppTest.from_file(str(RAIZ / "app.py"), default_timeout=120).run()


@pytest.mark.parametrize("pagina", list(PAGINA.values()))
def test_pagina_executa_sem_erro(pagina):
    at = iniciar()
    at.switch_page(pagina).run()
    assert not at.exception, [e.value for e in at.exception]


def test_mapa_todos_os_indicadores_com_metodo():
    at = iniciar()
    for opcao in at.selectbox[0].options:
        at.selectbox[0].set_value(opcao).run()
        assert not at.exception, opcao
        assert any("Função/algoritmo" in md.value for md in at.markdown), opcao


def test_cards_mostram_o_metodo():
    at = iniciar()
    cards = [md.value for md in at.markdown if 'class="card"' in md.value]
    assert cards and all("Método:" in c for c in cards)


def test_mapa_periodo_e_pesquisa_e_navegacao():
    at = iniciar()
    at.select_slider[0].set_value((pd.Timestamp("2021-01-01"), pd.Timestamp("2026-08-01"))).run()
    assert not at.exception
    at.selectbox(key="busca_mapa").set_value(TERESINA).run()
    assert any("### Teresina" in md.value for md in at.markdown)
    at.button[0].click().run()
    assert at.selectbox(key="sel_municipio").value == TERESINA


def test_municipio_troca_e_tabela_de_metodos():
    at = iniciar()
    at.switch_page(PAGINA["municipio"]).run()
    at.selectbox(key="sel_municipio").set_value(PICOS).run()
    assert not at.exception
    tabela = at.dataframe[0].value
    assert set(tabela["Função"]) >= {"scikit-learn RandomForestRegressor", "scikit-learn MLPRegressor"}
