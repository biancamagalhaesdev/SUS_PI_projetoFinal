"""Gráficos padronizados (Plotly), com rótulos em português e números no formato brasileiro."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.config import COR, COR_NIVEL, NIVEIS, PALETA_GRUPOS

LAYOUT = dict(template="plotly_white", separators=",.", font=dict(family="sans-serif", size=13, color="#1B2A3A"),
              margin=dict(l=10, r=10, t=56, b=10), hoverlabel=dict(bgcolor="white"),
              legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0))


def _finalizar(fig, titulo, x="", y="", altura=380):
    fig.update_layout(title=dict(text=titulo, x=0, font=dict(size=15)), xaxis_title=x, yaxis_title=y,
                      height=altura, **LAYOUT)
    return fig


def linha_mensal(serie: pd.Series, titulo: str, y: str = "Procedimentos", media_movel: bool = True,
                 destaque: tuple | None = None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines+markers", name="Produção mensal",
                             line=dict(color=COR["azul"], width=2), marker=dict(size=4),
                             hovertemplate="%{x|%m/%Y}: %{y:,.0f}<extra></extra>"))
    if media_movel and len(serie) >= 12:
        mm = serie.rolling(12).mean()
        fig.add_trace(go.Scatter(x=mm.index, y=mm.values, mode="lines", name="Média móvel de 12 meses",
                                 line=dict(color=COR["amarelo"], width=2, dash="dot"),
                                 hovertemplate="%{x|%m/%Y}: %{y:,.0f}<extra></extra>"))
    if destaque:
        fig.add_vrect(x0=destaque[0], x1=destaque[1], fillcolor=COR["vermelho"], opacity=0.07, line_width=0,
                      annotation_text=destaque[2], annotation_position="top left")
    return _finalizar(fig, titulo, "Mês de processamento", y)


def barras_anos(totais: pd.DataFrame, titulo: str, y: str = "Procedimentos"):
    """`totais`: colunas ano, total, rotulo (texto exibido no eixo)."""
    fig = go.Figure(go.Bar(x=totais["rotulo"], y=totais["total"], marker_color=COR["azul"],
                           hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
    return _finalizar(fig, titulo, "Ano", y)


def histograma_log(valores: pd.Series, titulo: str, x: str):
    v = np.log10(valores[valores > 0])
    fig = go.Figure(go.Histogram(x=v, nbinsx=30, marker_color=COR["azul"],
                                 hovertemplate="log10 entre %{x}: %{y} municípios<extra></extra>"))
    ticks = list(range(int(np.floor(v.min())), int(np.ceil(v.max())) + 1)) if len(v) else []
    fig.update_xaxes(tickvals=ticks, ticktext=[f"{10 ** t:,.0f}".replace(",", ".") for t in ticks])
    return _finalizar(fig, titulo, x, "Nº de municípios")


def barras_horizontais(nomes, valores, titulo: str, x: str, cor: str = COR["azul"], texto=None):
    fig = go.Figure(go.Bar(x=valores, y=nomes, orientation="h", marker_color=cor, text=texto,
                           textposition="auto", hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    return _finalizar(fig, titulo, x, "", altura=max(320, 26 * len(nomes) + 80))


def barras_niveis(contagem: pd.DataFrame, titulo: str):
    """`contagem`: índice = indicador; colunas = níveis."""
    fig = go.Figure()
    for nivel in NIVEIS:
        if nivel in contagem.columns:
            fig.add_trace(go.Bar(y=contagem.index, x=contagem[nivel], name=nivel, orientation="h",
                                 marker_color=COR_NIVEL[nivel], hovertemplate="%{y} — " + nivel + ": %{x}<extra></extra>"))
    fig.update_layout(barmode="stack")
    return _finalizar(fig, titulo, "Nº de municípios", "", altura=330)


def linhas_indice(series: dict, titulo: str):
    fig = go.Figure()
    estilos = [dict(color=COR["azul"], width=2.6), dict(color=COR["cinza"], width=2, dash="dot"),
               dict(color=COR["amarelo"], width=2, dash="dash")]
    for (nome, s), est in zip(series.items(), estilos):
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=nome, line=est,
                                 hovertemplate="%{x|%m/%Y}: %{y:.0f}<extra></extra>"))
    fig.add_hline(y=100, line_color="#B0B8C4", line_width=1)
    return _finalizar(fig, titulo, "Mês de processamento", "Índice (média do período = 100)")


def real_previsto(historico: pd.Series, previsoes: pd.DataFrame, proximo: pd.DataFrame, titulo: str, modelo: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historico.index, y=historico.values, mode="lines+markers", name="Produção registrada",
                             line=dict(color=COR["azul_escuro"], width=2), marker=dict(size=4),
                             hovertemplate="%{x|%m/%Y}: %{y:,.0f}<extra></extra>"))
    for periodo, cor in [("validação", COR["amarelo"]), ("teste", COR["vermelho"])]:
        p = previsoes[previsoes["periodo"] == periodo]
        if not p.empty:
            fig.add_trace(go.Scatter(x=p["competencia"], y=p["previsto"], mode="lines+markers",
                                     name=f"Previsto ({periodo})", line=dict(color=cor, width=2, dash="dot"),
                                     marker=dict(size=5), hovertemplate="%{x|%m/%Y}: %{y:,.0f}<extra></extra>"))
    if not proximo.empty:
        fig.add_trace(go.Scatter(x=proximo["competencia"], y=proximo["previsto"], mode="markers+text",
                                 name="Próximo mês (previsto)", marker=dict(size=12, color=COR["verde"], symbol="diamond"),
                                 text=[f"{v:,.0f}".replace(",", ".") for v in proximo["previsto"]], textposition="top center",
                                 hovertemplate="%{x|%m/%Y}: %{y:,.0f}<extra></extra>"))
    return _finalizar(fig, f"{titulo} — modelo: {modelo}", "Mês de processamento", "Procedimentos", altura=420)


def barras_metricas(df: pd.DataFrame, metrica: str, titulo: str):
    """`df`: colunas modelo, periodo, <metrica>."""
    fig = px.bar(df, x="modelo", y=metrica, color="periodo", barmode="group",
                 color_discrete_map={"validação": COR["azul_claro"], "teste": COR["azul"]},
                 labels={"modelo": "", "periodo": "Período", metrica: metrica})
    fig.update_traces(hovertemplate="%{x}: %{y:,.1f}<extra></extra>")
    return _finalizar(fig, titulo, "", metrica)


def dispersao(df: pd.DataFrame, x: str, y: str, cor: str, ordem: list, titulo: str, rx: str, ry: str,
              hover: str = "nome", log_x: bool = False):
    paleta = {g: PALETA_GRUPOS[i % len(PALETA_GRUPOS)] for i, g in enumerate(ordem)}
    fig = px.scatter(df, x=x, y=y, color=cor, category_orders={cor: ordem}, color_discrete_map=paleta,
                     hover_name=hover, log_x=log_x, labels={x: rx, y: ry, cor: "Grupo"})
    fig.update_traces(marker=dict(size=9, opacity=.8, line=dict(width=.5, color="white")))
    return _finalizar(fig, titulo, rx, ry, altura=430)


def caixas_por_grupo(df: pd.DataFrame, variavel: str, ordem: list, titulo: str, ry: str, log_y: bool = False):
    paleta = {g: PALETA_GRUPOS[i % len(PALETA_GRUPOS)] for i, g in enumerate(ordem)}
    fig = px.box(df, x="nome_grupo", y=variavel, color="nome_grupo", category_orders={"nome_grupo": ordem},
                 color_discrete_map=paleta, points="outliers", log_y=log_y, labels={"nome_grupo": "", variavel: ry})
    fig.update_layout(showlegend=False)
    return _finalizar(fig, titulo, "", ry, altura=360)
