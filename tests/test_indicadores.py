"""Indicadores descritivos e regras do resumo analítico."""
import numpy as np
import pandas as pd

from utils.indicators import (filtrar, fmt_compacto, fmt_int, fmt_mes, fmt_num, fmt_pct, indicadores_municipio,
                              indicadores_periodo, matriz, variacao_ano_anterior)

MESES = pd.date_range("2021-01-01", periods=36, freq="MS")


def producao_sintetica():
    linhas = []
    for cod, base in [("220001", 100.0), ("220002", 1000.0)]:
        for i, m in enumerate(MESES):
            linhas.append((cod, f"M{cod}", m, base * (1.1 if m.year == 2022 else 1.0)))
    return pd.DataFrame(linhas, columns=["codigo_ibge", "municipio", "competencia", "producao"])


def test_formatacao_brasileira():
    assert fmt_int(1234567) == "1.234.567"
    assert fmt_num(1234.5, 1) == "1.234,5"
    assert fmt_pct(0.125) == "+12,5%"
    assert fmt_compacto(3_090_000) == "3,09 mi"
    assert fmt_mes("2026-08-01") == "ago/2026"
    assert fmt_int(np.nan) == "—"


def test_variacao_ano_anterior():
    p = producao_sintetica()
    var, n = variacao_ano_anterior(p, filtrar(p, anos=[2022]))
    assert n == 12 and abs(var - 0.10) < 1e-9
    var, n = variacao_ano_anterior(p, filtrar(p, anos=[2021]))
    assert n == 0 and np.isnan(var)


def test_indicadores_periodo_variacao_e_cv():
    W = matriz(producao_sintetica())
    t = indicadores_periodo(W, "2022-01-01", "2022-12-01")
    assert np.allclose(t["variacao"], 0.10)
    assert np.allclose(t["cv"], 0.0)
    assert indicadores_periodo(W, MESES[0], MESES[-1])["variacao"].isna().all()   # sem período anterior


def test_tendencia_usa_mediana():
    s = pd.Series([100.0] * 24, index=pd.date_range("2024-01-01", periods=24, freq="MS"))
    s.iloc[-3] = 100_000                          # um pico isolado não cria tendência
    ind = indicadores_municipio(s)
    assert ind["tendencia_texto"] == "estabilidade"
    s2 = pd.Series([100.0] * 12 + [150.0] * 12, index=s.index)
    assert indicadores_municipio(s2)["tendencia_texto"] == "crescimento"
