"""Critérios de alerta."""
import numpy as np
import pandas as pd

from utils.alerts import _nivel, calcular
from utils.data_loader import ler_csv


def test_nivel_por_cauda():
    v = pd.Series([0.9, 0.3, 0.001, np.nan])
    n = _nivel(v, atencao=0.4, alerta=0.005, cauda="inferior")
    assert list(n[:3]) == ["Estável", "Atenção", "Alerta"] and pd.isna(n.iloc[3])
    n2 = _nivel(pd.Series([1.0, 1.5, 3.0]), atencao=1.44, alerta=2.55, cauda="superior")
    assert list(n2) == ["Estável", "Atenção", "Alerta"]


def test_limites_respeitam_a_regra_de_percentis():
    ind, lim = calcular(ler_csv("producao"), ler_csv("previsoes"))
    ref = ind["competencia"].between("2021-01-01", "2024-12-01")
    frac_atencao = (ind.loc[ref, "cv_12m"] >= lim["instabilidade"]["atencao"]).mean() / ind.loc[ref, "cv_12m"].notna().mean()
    assert 0.03 < frac_atencao < 0.07                      # cerca de 5% dos casos de referência
    assert lim["queda"]["alerta"] <= lim["queda"]["atencao"]
    assert lim["anomalia"]["alerta"] >= lim["anomalia"]["atencao"]


def test_classificacao_geral_e_a_mais_grave():
    ind = ler_csv("indicadores_alerta")
    ordem = {"Estável": 0, "Atenção": 1, "Alerta": 2}
    cols = ["nivel_queda", "nivel_instabilidade", "nivel_desvio", "nivel_anomalia"]
    gravidade = ind[cols].apply(lambda c: c.map(ordem)).max(axis=1)
    esperado = gravidade.map({v: k for k, v in ordem.items()})
    assert (esperado.fillna("—") == ind["nivel_geral"].fillna("—")).all()


def test_eventos_tem_justificativa_e_linguagem_adequada():
    ev = ler_csv("anomalias")
    assert ev["justificativa"].str.len().min() > 40
    proibidas = ["sem atendimento", "deficiência", "falta de médicos", "colapso"]
    texto = " ".join(ev["justificativa"]).lower()
    assert not any(p in texto for p in proibidas)
