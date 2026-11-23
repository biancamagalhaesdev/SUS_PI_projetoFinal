"""Indicadores descritivos da produção, formatação em português e regras do resumo analítico."""
import numpy as np
import pandas as pd

from utils.config import MESES_NOME

LIMIAR_TENDENCIA = 0.10       # ±10% entre a mediana dos últimos 12 meses e a dos 12 anteriores


# Formatação -------------------------------------------------------------------------
def fmt_int(x) -> str:
    return "—" if x is None or pd.isna(x) else f"{x:,.0f}".replace(",", ".")


def fmt_num(x, casas: int = 2) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(x, casas: int = 1, sinal: bool = True) -> str:
    if x is None or pd.isna(x) or np.isinf(x):
        return "—"
    s = f"{100 * x:+.{casas}f}%" if sinal else f"{100 * x:.{casas}f}%"
    return s.replace(".", ",")


def fmt_mes(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"{MESES_NOME[ts.month].lower()}/{ts.year}"


def fmt_compacto(x) -> str:
    """Números grandes de forma curta: 3,5 mi; 12,3 mil."""
    if x is None or pd.isna(x):
        return "—"
    if abs(x) >= 1e6:
        return fmt_num(x / 1e6, 2) + " mi"
    if abs(x) >= 1e4:
        return fmt_num(x / 1e3, 1) + " mil"
    return fmt_int(x)


# Estruturas -------------------------------------------------------------------------
def matriz(producao: pd.DataFrame) -> pd.DataFrame:
    """Município (código) × mês."""
    return producao.pivot(index="codigo_ibge", columns="competencia", values="producao").sort_index(axis=1)


def filtrar(producao: pd.DataFrame, anos=None, meses=None, codigos=None) -> pd.DataFrame:
    df = producao
    if anos:
        df = df[df["competencia"].dt.year.isin(anos)]
    if meses:
        df = df[df["competencia"].dt.month.isin(meses)]
    if codigos:
        df = df[df["codigo_ibge"].isin(codigos)]
    return df


# Visão geral ------------------------------------------------------------------------
def variacao_ano_anterior(producao: pd.DataFrame, filtrado: pd.DataFrame):
    """Variação do total filtrado em relação aos mesmos meses do ano anterior.

    Só entram na comparação os meses cujo mês correspondente do ano anterior existe na base.
    Retorna (variação, número de meses comparados).
    """
    meses_sel = pd.DatetimeIndex(filtrado["competencia"].unique())
    anteriores = meses_sel - pd.DateOffset(years=1)
    disponiveis = set(producao["competencia"].unique())
    pares = [(m, a) for m, a in zip(meses_sel, anteriores) if a in disponiveis]
    if not pares:
        return np.nan, 0
    codigos = filtrado["codigo_ibge"].unique()
    base = producao[producao["codigo_ibge"].isin(codigos)]
    atual = base[base["competencia"].isin([m for m, _ in pares])]["producao"].sum()
    antes = base[base["competencia"].isin([a for _, a in pares])]["producao"].sum()
    return (atual / antes - 1 if antes > 0 else np.nan), len(pares)


# Indicadores por período ------------------------------------------------------------
def indicadores_periodo(W: pd.DataFrame, ini, fim) -> pd.DataFrame:
    """Indicadores de cada município no período [ini, fim].

    A variação compara o total do período com o do período imediatamente anterior de mesma
    duração; fica indefinida quando esse período não existe na base.
    """
    ini, fim = pd.Timestamp(ini), pd.Timestamp(fim)
    janela = W.loc[:, ini:fim]
    n = janela.shape[1]
    media = janela.mean(axis=1)
    out = pd.DataFrame({
        "total": janela.sum(axis=1),
        "media": media,
        "cv": (janela.std(axis=1) / media.replace(0, np.nan)) if n > 1 else np.nan,
        "n_meses": n,
    })
    ini_ant = ini - pd.DateOffset(months=n)
    if ini_ant >= W.columns.min():
        anterior = W.loc[:, ini_ant:ini - pd.DateOffset(months=1)].sum(axis=1)
        out["variacao"] = out["total"] / anterior.replace(0, np.nan) - 1
    else:
        out["variacao"] = np.nan
    return out


def indicadores_municipio(serie: pd.Series) -> dict:
    """Indicadores de um município a partir de sua série mensal (índice = competência)."""
    serie = serie.sort_index()
    media = serie.mean()
    ind = {
        "total": serie.sum(), "media": media,
        "maximo": serie.max(), "mes_maximo": serie.idxmax(),
        "minimo": serie.min(), "mes_minimo": serie.idxmin(),
        "desvio": serie.std(), "cv": serie.std() / media if media > 0 else np.nan,
        "tendencia": np.nan, "tendencia_texto": "indisponível",
    }
    if len(serie) >= 24:
        # Medianas: um pico isolado não muda a tendência
        recente, anterior = serie.iloc[-12:].median(), serie.iloc[-24:-12].median()
        if anterior > 0:
            t = recente / anterior - 1
            ind["tendencia"] = t
            ind["tendencia_texto"] = ("crescimento" if t > LIMIAR_TENDENCIA else
                                      "redução" if t < -LIMIAR_TENDENCIA else "estabilidade")
    return ind


def serie_indice(serie: pd.Series) -> pd.Series:
    """Série em índice: média do período = 100 (permite comparar escalas diferentes)."""
    m = serie.mean()
    return serie / m * 100 if m > 0 else serie * np.nan


# Resumo analítico -------------------------------------------------------------------
def resumo_analitico(serie: pd.Series, ind: dict, cv_estado: pd.Series, cv_municipio: float,
                     grupo: dict | None, eventos: pd.DataFrame) -> list:
    """Frases geradas por regras explícitas a partir dos indicadores reais.

    - Tendência: mediana dos últimos 12 meses × mediana dos 12 anteriores; limiar de ±10%.
    - Variabilidade: posição do CV do município entre os CVs dos municípios do estado
      no mesmo período (quartis).
    - Grupo: produção média e CV de 2021–2024 dentro ou fora da faixa interquartil do grupo.
    - Reduções e variações atípicas: eventos dos critérios de alerta (página Alertas).
    """
    frases = []
    t = ind["tendencia"]
    if pd.notna(t):
        ini_rec = fmt_mes(serie.index[-12])
        fim_rec = fmt_mes(serie.index[-1])
        if ind["tendencia_texto"] == "estabilidade":
            frases.append(f"A mediana mensal da produção registrada de {ini_rec} a {fim_rec} variou {fmt_pct(t)} em "
                          f"relação à dos 12 meses anteriores, dentro da faixa de ±10%: comportamento relativamente estável.")
        else:
            frases.append(f"A produção registrada apresentou tendência de {ind['tendencia_texto']}: a mediana mensal de "
                          f"{ini_rec} a {fim_rec} foi {fmt_pct(t)} em relação à dos 12 meses anteriores.")

    if pd.notna(cv_municipio) and cv_estado.notna().sum() > 3:
        q1, q3 = cv_estado.quantile([.25, .75])
        if cv_municipio >= q3:
            frases.append(f"O município possui elevada variabilidade mensal: CV de {fmt_num(cv_municipio)}, entre os "
                          f"25% mais altos do estado no período.")
        elif cv_municipio <= q1:
            frases.append(f"O município possui baixa variabilidade mensal: CV de {fmt_num(cv_municipio)}, entre os "
                          f"25% mais baixos do estado no período.")
        else:
            frases.append(f"A variabilidade mensal é intermediária (CV de {fmt_num(cv_municipio)}), entre os quartis "
                          f"do estado ({fmt_num(q1)} e {fmt_num(q3)}).")

    if grupo:
        dentro = grupo["media_dentro"] and grupo["cv_dentro"]
        frases.append(f"O município pertence ao grupo “{grupo['nome']}”. Em 2021–2024, sua produção média e seu CV "
                      + ("estavam dentro da faixa interquartil do grupo: o comportamento se aproxima do típico do grupo."
                         if dentro else
                         "não estavam ambos dentro da faixa interquartil do grupo: o comportamento se afasta "
                         "do típico do grupo em ao menos uma dessas características."))

    quedas = eventos[eventos["indicador"] == "Queda expressiva"].sort_values("competencia")
    if not quedas.empty:
        ult = quedas.iloc[-1]
        frases.append(f"Foi identificada redução expressiva da produção registrada em {len(quedas)} mês(es); "
                      f"o mais recente em {fmt_mes(ult['competencia'])} (classificação: {ult['classificacao']}).")

    atipicos = eventos[eventos["indicador"] == "Anomalia (Isolation Forest)"].sort_values("competencia")
    if not atipicos.empty:
        frases.append(f"Foram identificadas variações atípicas em {len(atipicos)} mês(es) pelo Isolation Forest; "
                      f"a mais recente em {fmt_mes(atipicos.iloc[-1]['competencia'])}.")
    else:
        frases.append("Não foram identificadas variações atípicas pelo Isolation Forest no período.")
    return frases


def posicao_no_grupo(agr: pd.DataFrame, codigo: str) -> dict | None:
    """Compara produção média e CV (2021–2024) do município com a faixa interquartil do seu grupo."""
    linha = agr[agr["codigo_ibge"] == codigo]
    if linha.empty:
        return None
    linha = linha.iloc[0]
    membros = agr[agr["nome_grupo"] == linha["nome_grupo"]]
    m1, m3 = membros["media_mensal"].quantile([.25, .75])
    c1, c3 = membros["cv"].quantile([.25, .75])
    return {"nome": linha["nome_grupo"],
            "media_dentro": m1 <= linha["media_mensal"] <= m3,
            "cv_dentro": c1 <= linha["cv"] <= c3}
