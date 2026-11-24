"""Página inicial: indicadores gerais e mapa interativo dos municípios, com o método de cada indicador."""
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from utils import charts
from utils.config import PAGINA
from utils.contexto import abrir_analise, base, definir_municipio, municipio_atual, nomes_municipios
from utils.data_loader import carregar, carregar_geojson, carregar_json, exigir_dados
from utils.indicators import fmt_compacto, fmt_int, fmt_mes, fmt_num, fmt_pct, indicadores_periodo
from utils.maps import colorir_categorias, colorir_niveis, colorir_quantis, colorir_variacao, construir_mapa
from utils.metodos import INDICADOR_PARA_NIVEL, m
from utils.ui import aviso_interpretacao, cabecalho, card, legenda_metodo, linha_de_cards, selo_nivel

cabecalho("SUS Inteligente — Piauí",
          "Produção ambulatorial registrada, previsões, grupos e alertas dos 224 municípios do Piauí")
prod, cat, W = exigir_dados(base)
geo = exigir_dados(carregar_geojson)
ind = exigir_dados(carregar, "indicadores_alerta")
agr = exigir_dados(carregar, "agrupamentos")
prev = exigir_dados(carregar, "previsoes")
meta = exigir_dados(carregar_json, "metadados")
info_agr = exigir_dados(carregar_json, "agrupamento_info")
nomes = nomes_municipios(cat)
meses = list(W.columns)
modelo = meta["modelo_escolhido"]
mes_previsto = pd.Timestamp(meta["mes_previsto"] + "-01")
proximo = prev[prev["escolhido"].astype(bool) & (prev["periodo"] == "próximo mês")].set_index("codigo_ibge")["previsto"]
grupo = agr.set_index("codigo_ibge")["nome_grupo"]

INDICADORES = ["producao_total", "media_mensal", "variacao", "cv", "previsao", "grupo", "alerta"]


def ao_buscar():
    if st.session_state["busca_mapa"]:
        definir_municipio(st.session_state["busca_mapa"])
        st.session_state["zoom_mapa"] = True


# Controles ---------------------------------------------------------------------------
with st.container(border=True):
    c1, c2 = st.columns([1.3, 2])
    chave = c1.selectbox("Indicador do mapa", INDICADORES, format_func=lambda k: m(k).rotulo)
    ini, fim = c2.select_slider("Período", options=meses, value=(meses[-12], meses[-1]), format_func=fmt_mes)
    c3, c4 = st.columns([2, 1.3])
    c3.selectbox("Pesquisar município", cat["codigo_ibge"], index=None, format_func=nomes.get,
                 placeholder="Digite o nome do município", key="busca_mapa", on_change=ao_buscar)
    destacar = c4.toggle("Destacar municípios em alerta", value=True)
    legenda_metodo(m(chave).calculo, m(chave).funcao)

# Indicadores gerais ------------------------------------------------------------------
tab = indicadores_periodo(W, ini, fim)
no_fim = ind[ind["competencia"] == fim].set_index("codigo_ibge")
n_alerta = int((no_fim["nivel_geral"] == "Alerta").sum())
n_atencao = int((no_fim["nivel_geral"] == "Atenção").sum())
linha_de_cards([
    ("Produção registrada no período", fmt_compacto(tab["total"].sum()),
     f"{fmt_mes(ini)} a {fmt_mes(fim)}", m("producao_total").funcao),
    ("Média mensal do estado", fmt_compacto(tab["total"].sum() / tab["n_meses"].iloc[0]),
     "procedimentos por mês", m("media_mensal").funcao),
    ("Municípios em alerta", fmt_int(n_alerta), f"{n_atencao} em atenção · {fmt_mes(fim)}", m("alerta").funcao),
    (f"Previsão do estado para {fmt_mes(mes_previsto)}", fmt_compacto(proximo.sum()),
     "soma das previsões dos municípios", m("previsao").funcao),
], por_linha=4)

# Valores do indicador escolhido ------------------------------------------------------
aviso = None
if chave == "producao_total":
    valor = tab["total"]
    cores, legenda = colorir_quantis(valor, fmt_compacto)
    texto = valor.map(lambda v: f"{fmt_int(v)} procedimentos")
elif chave == "media_mensal":
    valor = tab["media"]
    cores, legenda = colorir_quantis(valor, fmt_compacto)
    texto = valor.map(lambda v: f"{fmt_int(v)} procedimentos/mês")
elif chave == "variacao":
    valor = tab["variacao"]
    cores, legenda = colorir_variacao(valor, lambda v: fmt_pct(v, 0))
    texto = valor.map(fmt_pct)
    if valor.isna().all():
        aviso = "Não há na base um período anterior de mesma duração; encurte o período ou mova o início."
elif chave == "cv":
    valor = tab["cv"]
    cores, legenda = colorir_quantis(valor, fmt_num)
    texto = valor.map(lambda v: f"CV de {fmt_num(v)}")
elif chave == "previsao":
    valor = proximo.reindex(tab.index)
    cores, legenda = colorir_quantis(valor, fmt_compacto)
    texto = valor.map(lambda v: f"{fmt_int(v)} procedimentos previstos para {fmt_mes(mes_previsto)}")
    aviso = (f"A previsão é para {fmt_mes(mes_previsto)}, o mês seguinte ao fim da base, e não depende do período "
             "selecionado. Os meses de jun–ago/2026 foram atípicos, o que reduz a confiança nessa previsão.")
elif chave == "grupo":
    valor = grupo.reindex(tab.index)
    cores, legenda = colorir_categorias(valor, info_agr["ordem_grupos"])
    texto = valor.fillna("sem grupo")
else:
    valor = no_fim["nivel_geral"].reindex(tab.index)
    cores, legenda = colorir_niveis(valor)
    texto = valor.fillna("sem classificação").map(lambda v: f"{v} em {fmt_mes(fim)}")

tabela = pd.DataFrame({"codigo_ibge": tab.index, "cor": cores.reindex(tab.index).values,
                       "valor_fmt": texto.reindex(tab.index).values})
em_alerta = set(no_fim.index[no_fim["nivel_geral"] == "Alerta"]) if destacar else set()
selecionado = municipio_atual()
zoom = st.session_state.pop("zoom_mapa", False)

# Mapa e painel -----------------------------------------------------------------------
if aviso:
    st.info(aviso)
col_mapa, col_painel = st.columns([2.1, 1])
with col_mapa:
    mapa = construir_mapa(geo, tabela, m(chave).rotulo, legenda, destaque=em_alerta, selecionado=selecionado,
                          enquadrar=zoom, metodo=m(chave).funcao)
    saida = st_folium(mapa, key="mapa_pi", height=600, use_container_width=True,
                      returned_objects=["last_active_drawing"])
    st.caption("Passe o mouse (ou toque, no celular) sobre um município para ver o valor; clique para abrir o painel, "
               "que aparece ao lado do mapa no computador e abaixo dele no celular. "
               "Contorno vermelho: classificação geral Alerta no último mês do período.")

clique = (saida or {}).get("last_active_drawing")
if clique and clique.get("properties", {}).get("codigo_ibge"):
    cod = clique["properties"]["codigo_ibge"]
    if cod != st.session_state.get("ultimo_clique"):
        st.session_state["ultimo_clique"] = cod
        definir_municipio(cod)
        st.rerun()

with col_painel:
    cod = municipio_atual()
    if not cod:
        st.info("Clique em um município no mapa ou use a pesquisa para ver os detalhes.")
    else:
        t = tab.loc[cod]
        with st.container(border=True):
            st.markdown(f"### {nomes[cod]}")
            situacao = no_fim["nivel_geral"].get(cod)
            st.markdown(f"Grupo: **{grupo.get(cod, '—')}**" +
                        (f" &nbsp; {selo_nivel(situacao)}" if isinstance(situacao, str) else ""),
                        unsafe_allow_html=True)
            st.caption(f"Grupo — {m('grupo').funcao}")
            a, b = st.columns(2)
            with a:
                card("Produção no período", fmt_compacto(t["total"]), metodo=m("producao_total").funcao)
            with b:
                card("Média mensal", fmt_compacto(t["media"]), metodo=m("media_mensal").funcao)
            a, b = st.columns(2)
            with a:
                card("Variação", fmt_pct(t["variacao"]), metodo=m("variacao").funcao)
            with b:
                card("Volatilidade", f"CV {fmt_num(t['cv'])}", metodo=m("cv").funcao)
            card(f"Previsão para {fmt_mes(mes_previsto)}", f"{fmt_int(proximo.get(cod))} procedimentos",
                 metodo=m("previsao").funcao)
            fig = charts.linha_mensal(W.loc[cod], "Evolução mensal", media_movel=False)
            fig.update_layout(height=210, margin=dict(l=0, r=0, t=36, b=0), showlegend=False)
            st.plotly_chart(fig, width="stretch")
            if cod in no_fim.index:
                st.markdown(f"**Alertas em {fmt_mes(fim)}**")
                for k, col in INDICADOR_PARA_NIVEL.items():
                    nivel = no_fim.loc[cod, col]
                    if isinstance(nivel, str):
                        st.markdown(f"{selo_nivel(nivel)} {m(k).rotulo} <span style='color:#5B6B7F;font-size:.8rem'>"
                                    f"— {m(k).funcao}</span>", unsafe_allow_html=True)
            if st.button("Ver detalhes do município", type="primary", width="stretch"):
                abrir_analise(cod, PAGINA["municipio"])

aviso_interpretacao()
