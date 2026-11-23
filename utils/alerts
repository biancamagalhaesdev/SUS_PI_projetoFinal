"""Critérios dos alertas analíticos.

Regra única para todos os indicadores: o valor de cada município em cada mês é comparado com
a distribuição do mesmo indicador em um período de referência.

  - Atenção: mais extremo que 95% dos casos de referência.
  - Alerta:  mais extremo que 99% dos casos de referência.
  - Estável: demais casos.

Indicadores
  1. Queda expressiva: média dos últimos 3 meses ÷ mediana dos 12 meses anteriores (cauda inferior).
  2. Instabilidade mensal: coeficiente de variação dos últimos 12 meses (cauda superior).
  3. Desvio em relação à previsão: |log(1 + real) − log(1 + previsto)|, com as previsões fora da
     amostra do modelo escolhido no notebook (cauda superior). Referência: validação de 2025.
  4. Anomalia (Isolation Forest): escore de anomalia de cada mês, a partir de três variações
     relativas ao próprio município (cauda superior).

Referência dos indicadores 1, 2 e 4: jan/2021 a dez/2024, o período de treinamento do notebook.
Os alertas indicam alterações estatísticas na produção registrada; não indicam deficiência de atendimento.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from utils.indicators import fmt_int, fmt_num, fmt_pct, matriz

REF_INI, REF_FIM = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-12-01")
DESVIO_REF_INI, DESVIO_REF_FIM = pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-01")
P_ATENCAO, P_ALERTA = 0.95, 0.99
SEED = 42
ORDEM = {"Estável": 0, "Atenção": 1, "Alerta": 2}
NOME = {"queda": "Queda expressiva", "instabilidade": "Instabilidade mensal",
        "desvio": "Desvio em relação à previsão", "anomalia": "Anomalia (Isolation Forest)"}


def _para_longo(T: pd.DataFrame, nome: str) -> pd.DataFrame:
    """Meses × municípios → formato longo (mantém valores ausentes)."""
    return (T.rename_axis("competencia").reset_index()
             .melt(id_vars="competencia", var_name="codigo_ibge", value_name=nome))


def indicadores_da_serie(producao: pd.DataFrame) -> pd.DataFrame:
    """Indicadores 1, 2 e os atributos do Isolation Forest, com dados até o próprio mês."""
    T = matriz(producao).T.astype(float)                  # meses × municípios
    media3 = T.rolling(3).mean()
    mediana_ant = T.shift(3).rolling(12).median()
    queda = media3 / mediana_ant.where(mediana_ant > 0)
    m12, s12 = T.rolling(12).mean(), T.rolling(12).std()
    cv12 = s12 / m12.where(m12 > 0)
    L = np.log1p(T)
    f_mediana = L - np.log1p(T.shift(1).rolling(12).median())   # vs. mediana dos 12 meses anteriores
    f_mes = L - L.shift(1)                                        # vs. mês anterior
    f_ano = L - L.shift(12)                                       # vs. mesmo mês do ano anterior
    partes = [_para_longo(T, "producao"), _para_longo(queda, "queda_razao"), _para_longo(cv12, "cv_12m"),
              _para_longo(f_mediana, "var_mediana12"), _para_longo(f_mes, "var_mes_anterior"),
              _para_longo(f_ano, "var_ano_anterior")]
    df = partes[0]
    for p in partes[1:]:
        df = df.merge(p, on=["competencia", "codigo_ibge"])
    return df


def desvio_previsao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Indicador 3: desvio entre real e previsto pelo modelo escolhido (validação e teste)."""
    p = previsoes[previsoes["escolhido"].astype(bool) & previsoes["periodo"].isin(["validação", "teste"])].copy()
    p["desvio_log"] = np.log1p(p["real"]) - np.log1p(p["previsto"])
    return p[["codigo_ibge", "competencia", "modelo", "real", "previsto", "desvio_log"]]


def _nivel(valor: pd.Series, atencao: float, alerta: float, cauda: str) -> pd.Series:
    if cauda == "inferior":
        nivel = np.where(valor <= alerta, "Alerta", np.where(valor <= atencao, "Atenção", "Estável"))
    else:
        nivel = np.where(valor >= alerta, "Alerta", np.where(valor >= atencao, "Atenção", "Estável"))
    return pd.Series(nivel, index=valor.index).where(valor.notna())


def calcular(producao: pd.DataFrame, previsoes: pd.DataFrame):
    """Retorna (indicadores por município e mês, limites usados)."""
    df = indicadores_da_serie(producao)
    ref = df["competencia"].between(REF_INI, REF_FIM)

    lim = {}
    q = df.loc[ref, "queda_razao"].dropna()
    lim["queda"] = {"atencao": float(q.quantile(1 - P_ATENCAO)), "alerta": float(q.quantile(1 - P_ALERTA)),
                    "cauda": "inferior", "n_referencia": int(len(q))}
    c = df.loc[ref, "cv_12m"].dropna()
    lim["instabilidade"] = {"atencao": float(c.quantile(P_ATENCAO)), "alerta": float(c.quantile(P_ALERTA)),
                            "cauda": "superior", "n_referencia": int(len(c))}

    atributos = ["var_mediana12", "var_mes_anterior", "var_ano_anterior"]
    completos = df[atributos].notna().all(axis=1)
    floresta = IsolationForest(n_estimators=300, random_state=SEED).fit(df.loc[ref & completos, atributos])
    df["escore_anomalia"] = np.nan
    df.loc[completos, "escore_anomalia"] = -floresta.score_samples(df.loc[completos, atributos])
    s = df.loc[ref & completos, "escore_anomalia"]
    lim["anomalia"] = {"atencao": float(s.quantile(P_ATENCAO)), "alerta": float(s.quantile(P_ALERTA)),
                       "cauda": "superior", "n_referencia": int(len(s)),
                       "referencia_inicio": df.loc[ref & completos, "competencia"].min().strftime("%Y-%m")}

    dv = desvio_previsao(previsoes)
    df = df.merge(dv, on=["codigo_ibge", "competencia"], how="left")
    d_ref = df.loc[df["competencia"].between(DESVIO_REF_INI, DESVIO_REF_FIM), "desvio_log"].abs().dropna()
    lim["desvio"] = {"atencao": float(d_ref.quantile(P_ATENCAO)), "alerta": float(d_ref.quantile(P_ALERTA)),
                     "cauda": "superior", "n_referencia": int(len(d_ref)),
                     "modelo": str(dv["modelo"].iloc[0]) if not dv.empty else ""}

    df["nivel_queda"] = _nivel(df["queda_razao"], lim["queda"]["atencao"], lim["queda"]["alerta"], "inferior")
    df["nivel_instabilidade"] = _nivel(df["cv_12m"], lim["instabilidade"]["atencao"], lim["instabilidade"]["alerta"], "superior")
    df["nivel_desvio"] = _nivel(df["desvio_log"].abs(), lim["desvio"]["atencao"], lim["desvio"]["alerta"], "superior")
    df["nivel_anomalia"] = _nivel(df["escore_anomalia"], lim["anomalia"]["atencao"], lim["anomalia"]["alerta"], "superior")
    niveis = df[["nivel_queda", "nivel_instabilidade", "nivel_desvio", "nivel_anomalia"]]
    gravidade = niveis.apply(lambda col: col.map(ORDEM)).max(axis=1)
    df["nivel_geral"] = gravidade.map({v: k for k, v in ORDEM.items()})

    lim["regra"] = {"atencao": f"mais extremo que {P_ATENCAO:.0%} dos casos de referência",
                    "alerta": f"mais extremo que {P_ALERTA:.0%} dos casos de referência",
                    "referencia": f"{REF_INI:%Y-%m} a {REF_FIM:%Y-%m} (desvio: {DESVIO_REF_INI:%Y-%m} a {DESVIO_REF_FIM:%Y-%m})"}
    return df.sort_values(["codigo_ibge", "competencia"]).reset_index(drop=True), lim


def _pct_de_log(x) -> float:
    return float(np.expm1(x))


def eventos(df: pd.DataFrame, lim: dict, nomes: pd.Series) -> pd.DataFrame:
    """Tabela de eventos (Atenção ou Alerta), com a justificativa de cada classificação."""
    linhas = []
    for _, r in df.iterrows():
        cod, mes = r["codigo_ibge"], r["competencia"]
        if r["nivel_queda"] in ("Atenção", "Alerta"):
            L = lim["queda"]
            linhas.append((cod, mes, NOME["queda"], r["queda_razao"], f"redução de {fmt_pct(1 - r['queda_razao'], 0, False)}",
                           r["nivel_queda"],
                           f"A média dos últimos 3 meses equivale a {fmt_pct(r['queda_razao'], 0, False)} da mediana dos "
                           f"12 meses anteriores. Limites: Atenção ≤ {fmt_pct(L['atencao'], 0, False)}; "
                           f"Alerta ≤ {fmt_pct(L['alerta'], 0, False)} (percentis 5 e 1 de 2021–2024)."))
        if r["nivel_instabilidade"] in ("Atenção", "Alerta"):
            L = lim["instabilidade"]
            linhas.append((cod, mes, NOME["instabilidade"], r["cv_12m"], f"CV de {fmt_num(r['cv_12m'])}",
                           r["nivel_instabilidade"],
                           f"O coeficiente de variação dos últimos 12 meses é {fmt_num(r['cv_12m'])}. Limites: "
                           f"Atenção ≥ {fmt_num(L['atencao'])}; Alerta ≥ {fmt_num(L['alerta'])} "
                           f"(percentis 95 e 99 de 2021–2024)."))
        if r["nivel_desvio"] in ("Atenção", "Alerta"):
            L = lim["desvio"]
            rel = _pct_de_log(r["desvio_log"])
            sentido = "acima" if r["desvio_log"] > 0 else "abaixo"
            linhas.append((cod, mes, NOME["desvio"], r["desvio_log"], f"{fmt_pct(rel, 0)} em relação ao previsto",
                           r["nivel_desvio"],
                           f"Produção registrada de {fmt_int(r['real'])} contra {fmt_int(r['previsto'])} previstos pelo "
                           f"modelo {r['modelo']} ({sentido} do previsto). Limites do desvio em log: Atenção ≥ "
                           f"{fmt_num(L['atencao'])}; Alerta ≥ {fmt_num(L['alerta'])} (percentis 95 e 99 dos desvios de 2025)."))
        if r["nivel_anomalia"] in ("Atenção", "Alerta"):
            L = lim["anomalia"]
            linhas.append((cod, mes, NOME["anomalia"], r["escore_anomalia"], f"escore de {fmt_num(r['escore_anomalia'], 3)}",
                           r["nivel_anomalia"],
                           f"Combinação atípica de variações: {fmt_pct(_pct_de_log(r['var_mes_anterior']), 0)} em relação ao "
                           f"mês anterior, {fmt_pct(_pct_de_log(r['var_ano_anterior']), 0)} em relação ao mesmo mês do ano "
                           f"anterior e {fmt_pct(_pct_de_log(r['var_mediana12']), 0)} em relação à mediana dos 12 meses "
                           f"anteriores. Limites do escore: Atenção ≥ {fmt_num(L['atencao'], 3)}; Alerta ≥ "
                           f"{fmt_num(L['alerta'], 3)} (percentis 95 e 99 de 2022–2024)."))
    ev = pd.DataFrame(linhas, columns=["codigo_ibge", "competencia", "indicador", "valor", "intensidade",
                                       "classificacao", "justificativa"])
    ev.insert(1, "municipio", ev["codigo_ibge"].map(nomes))
    return ev.sort_values(["competencia", "codigo_ibge", "indicador"], ascending=[False, True, True]).reset_index(drop=True)
