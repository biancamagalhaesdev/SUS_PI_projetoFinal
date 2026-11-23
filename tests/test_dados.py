"""Integridade dos arquivos de dados e da junção geográfica."""
import json

import pandas as pd
import pytest

from utils.config import N_MUNICIPIOS_PI
from utils.data_loader import ErroDados, catalogo_municipios, ler_csv, ler_geojson, ler_json


def test_producao_completa():
    p = ler_csv("producao")
    assert p["codigo_ibge"].nunique() == N_MUNICIPIOS_PI
    assert p["competencia"].nunique() == 68
    assert len(p) == N_MUNICIPIOS_PI * 68
    assert (p["producao"] >= 0).all()
    assert not p.duplicated(["codigo_ibge", "competencia"]).any()


def test_juncao_pelo_codigo_ibge():
    cat = catalogo_municipios(ler_csv("producao"), ler_geojson())
    assert len(cat) == N_MUNICIPIOS_PI
    assert cat["codigo_ibge7"].str[:6].eq(cat["codigo_ibge"]).all()     # 7 dígitos = 6 dígitos + verificador
    assert "Nazária" in set(cat["nome"])


@pytest.mark.parametrize("nome", ["previsoes", "metricas", "agrupamentos", "indicadores_alerta", "anomalias"])
def test_resultados_carregam(nome):
    assert len(ler_csv(nome)) > 0


def test_previsoes_cobrem_todos_os_modelos_e_periodos():
    prev = ler_csv("previsoes")
    assert set(prev["periodo"]) == {"validação", "teste", "próximo mês"}
    por_modelo = prev.groupby(["modelo", "periodo"]).size().unstack()
    assert (por_modelo["próximo mês"] == N_MUNICIPIOS_PI).all()
    assert prev.loc[prev["periodo"] == "próximo mês", "real"].isna().all()
    assert prev["escolhido"].astype(bool).groupby(prev["modelo"]).all().sum() == 1


def test_metricas_reproduzem_as_previsoes():
    prev, met = ler_csv("previsoes"), ler_csv("metricas")
    for _, linha in met.iterrows():
        p = prev[(prev["modelo"] == linha["modelo"]) & (prev["periodo"] == linha["periodo"])]
        assert abs((p["real"] - p["previsto"]).abs().mean() - linha["MAE"]) < 1e-6


def test_erro_claro_quando_arquivo_falta(tmp_path, monkeypatch):
    import utils.data_loader as dl
    falso = {**dl.ARQUIVOS, "producao": (tmp_path / "nao_existe.csv", ["codigo_ibge"])}
    monkeypatch.setattr(dl, "ARQUIVOS", falso)
    with pytest.raises(ErroDados, match="não encontrado"):
        dl.ler_csv("producao")


def test_metadados_e_limites():
    meta, lim = ler_json("metadados"), ler_json("limites_alerta")
    assert meta["mes_previsto"] == "2026-09"
    for k in ["queda", "instabilidade", "desvio", "anomalia"]:
        assert set(lim[k]) >= {"atencao", "alerta", "cauda"}
