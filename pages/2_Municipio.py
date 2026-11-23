"""Detalhes de um município: indicadores, resumo analítico, previsões e alertas, com o método de cada número."""
import numpy as np
import pandas as pd
import streamlit as st

from utils import charts
from utils.contexto import base, nomes_municipios, seletor_municipio
from utils.data_loader import carregar, carregar_json, exigir_dados
from utils.indicators import (fmt_compacto, fmt_int, fmt_mes, fmt_num, fmt_pct, indicadores_municipio,
                              indicadores_periodo, posicao_no_grupo, resumo_analitico)
from utils.metodos import NOME_EVENTO, m
from utils.ui import aviso_interpretacao, cabecalho, linha_de_cards, selo_nivel

cabecalho("Município", "Indicadores, previsões e alertas de um município, com o método usado em cada número")
prod, cat, W = exigir_dados(base)
agr = exigir_dados(carregar, "agrupamentos")
prev = exigir_dados(carregar, "previsoes")
ev = exigir_dados(carregar, "anomalias")
ind_alerta = exigir_dados(carregar, "indicadores_alerta")
meta = exigir_dados(carregar_json, "metadados")
nomes = nomes_municipios(cat)
modelo = meta["modelo_escolhido"]

cod = seletor_municipio(cat, "sel_municipio")
serie = W.loc[cod]
ind = indicadores_municipio(serie)
grupo = agr.set_index("codigo_ibge").loc[cod, "nome_grupo"]
p_mun = prev[prev["codigo_ibge"] == cod]
prox = p_mun[(p_mun["modelo"] == modelo) & (p_mun["periodo"] == "próximo mês")]

# Indicadores -------------------------------------------------------------------------
linha_de_cards([
    ("Produção total", fmt_compacto(ind["total"]), "jan/2021 a ago/2026", m("producao_total").funcao),
    ("Média mensal", fmt_compacto(ind["media"]), "procedimentos por mês", m("media_mensal").funcao),
    ("Tendência", ind["tendencia_texto"].capitalize(), f"{fmt_pct(ind['tendencia'])} (últimos 12 meses)",
     m("tendencia").funcao),
    ("Volatilidade", f"CV {fmt_num(ind['cv'])}", f"maior mês: {fmt_compacto(ind['maximo'])} ({fmt_mes(ind['mes_maximo'])})",
     m("cv").funcao),
    ("Grupo territorial", grupo, "perfil de 2021–2024", m("grupo").funcao),
    (f"Previsão para {fmt_mes(prox['competencia'].iloc[0])}" if not prox.empty else "Previsão",
     f"{fmt_int(prox['previsto'].iloc[0])}" if not prox.empty else "—", "procedimentos",
     m("previsao").funcao),
], por_linha=3)

# Resumo analítico --------------------------------------------------------------------
cv_estado = indicadores_periodo(W, W.columns[0], W.columns[-1])["cv"]
frases = resumo_analitico(serie, ind, cv_estado, cv_estado.get(cod), posicao_no_grupo(agr, cod),
                          ev[ev["codigo_ibge"] == cod])
with st.container(border=True):
    st.markdown("#### Resumo analítico")
    st.markdown("\n".join(f"- {f}" for f in frases))
    st.caption("Frases geradas por regras fixas a partir dos indicadores: tendência pela razão entre medianas "
               "(limiar de ±10%), variabilidade pelos quartis do CV no estado, grupo pela faixa interquartil do "
               "K-Means e variações atípicas pelo Isolation Forest.")

# Previsões ---------------------------------------------------------------------------
st.markdown("#### Produção registrada e previsões")
completo = st.toggle("Mostrar desde jan/2021", value=False)
hist = serie if completo else serie.loc["2024-01-01":]
fora = p_mun[(p_mun["modelo"] == modelo) & p_mun["periodo"].isin(["validação", "teste"])]
st.plotly_chart(charts.real_previsto(hist, fora, prox, f"Real × previsto — {nomes[cod]}", modelo), width="stretch")
st.caption(f"Previsões de um mês à frente com {modelo} ({m(modelo).funcao}): validação em 2025, teste em "
           "jan–ago/2026 e previsão do mês seguinte ao fim da base.")

erro = p_mun[p_mun["periodo"].isin(["validação", "teste"])].copy()
erro["abs"] = (erro["real"] - erro["previsto"]).abs()
linhas = []
for nome in ["Naive sazonal", "Regressão Linear", "Random Forest", "Rede neural MLP"]:
    e = erro[erro["modelo"] == nome]
    if e.empty:
        continue
    pos = e["real"] > 0
    mape = 100 * (e.loc[pos, "abs"] / e.loc[pos, "real"]).mean() if pos.any() else np.nan
    linhas.append({"Método": nome + (" ★" if nome == modelo else ""), "Como funciona": m(nome).calculo,
                   "Função": m(nome).funcao, "MAE": fmt_int(e["abs"].mean()), "MAPE (%)": fmt_num(mape, 1)})
st.markdown("**Erro de cada método neste município (jan/2025 a ago/2026)**")
st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
st.caption(f"★ modelo escolhido no notebook pelo menor erro na validação. MAE: {m('mae').funcao}; "
           f"MAPE: {m('mape').calculo.lower()}.")

# Alertas -----------------------------------------------------------------------------
st.markdown("#### Alertas")
ultimo = ind_alerta[ind_alerta["codigo_ibge"] == cod].sort_values("competencia").iloc[-1]
st.markdown(f"Situação em {fmt_mes(ultimo['competencia'])}: {selo_nivel(ultimo['nivel_geral'])} "
            f"<span style='color:#5B6B7F;font-size:.85rem'>— {m('alerta').funcao}</span>", unsafe_allow_html=True)
evm = ev[ev["codigo_ibge"] == cod]
if evm.empty:
    st.success("Nenhum alerta ou ponto de atenção identificado no período.")
else:
    funcao = {nome: m(k).funcao for k, nome in NOME_EVENTO.items()}
    tabela = pd.DataFrame({"Mês": evm["competencia"].map(fmt_mes), "Indicador": evm["indicador"],
                           "Método": evm["indicador"].map(funcao), "Classificação": evm["classificacao"],
                           "Justificativa": evm["justificativa"]})
    st.dataframe(tabela, hide_index=True, width="stretch", height=min(380, 38 * len(tabela) + 40))
aviso_interpretacao()
