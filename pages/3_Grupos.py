"""Grupos de municípios com padrões semelhantes (aprendizado não supervisionado)."""
import pandas as pd
import streamlit as st

from utils import charts
from utils.contexto import base, nomes_municipios
from utils.data_loader import carregar, carregar_json, exigir_dados
from utils.indicators import fmt_compacto, fmt_num
from utils.metodos import m
from utils.ui import cabecalho, linha_de_cards

cabecalho("Grupos de municípios", "Municípios com padrões semelhantes de produção, encontrados por K-Means")
prod, cat, W = exigir_dados(base)
agr = exigir_dados(carregar, "agrupamentos")
info = exigir_dados(carregar_json, "agrupamento_info")
nomes = nomes_municipios(cat)
agr = agr.assign(nome=agr["codigo_ibge"].map(nomes))
ordem, k = info["ordem_grupos"], info["k_final"]
selecao = pd.DataFrame(info["selecao_k"]).set_index("k")
col_sil = [c for c in selecao.columns if "silhueta" in c and "K-Means" in c][0]

linha_de_cards([
    ("Grupos encontrados", str(k), "escolhidos pela maior silhueta entre k = 2 e 8", m("grupo").funcao),
    ("Silhueta", fmt_num(selecao.loc[k, col_sil]), "separação moderada entre os grupos", m("silhueta").funcao),
    ("Variância nos 2 eixos do gráfico", f"{sum(info['pca_variancia_explicada']):.0%}".replace(".", ","),
     "usada só para desenhar o gráfico", m("pca").funcao),
], por_linha=3)

st.markdown("**Características usadas (jan/2021 a dez/2024):** produção média, desvio padrão, coeficiente de variação, "
            "crescimento, produção máxima, produção mínima e amplitude sazonal. As medidas de tamanho passam por "
            "logaritmo e todas são padronizadas antes do agrupamento. Os nomes foram dados depois de examinar os grupos.")

resumo = agr.groupby("nome_grupo").agg(municipios=("codigo_ibge", "size"), media=("media_mensal", "median"),
                                       cv=("cv", "median"), crescimento=("crescimento", "median")).reindex(ordem)
st.dataframe(pd.DataFrame({"Municípios": resumo["municipios"],
                           "Produção mensal (mediana)": resumo["media"].map(fmt_compacto),
                           "Volatilidade — CV (mediana)": resumo["cv"].map(fmt_num),
                           "Crescimento 2021→2024 (mediana)": resumo["crescimento"].map(fmt_num)}), width="stretch")

c1, c2 = st.columns(2)
with c1:
    v1, v2 = info["pca_variancia_explicada"]
    st.plotly_chart(charts.dispersao(agr, "pca1", "pca2", "nome_grupo", ordem, "Municípios nos dois eixos da PCA",
                                     f"Eixo 1 — porte ({v1:.0%})", f"Eixo 2 — instabilidade ({v2:.0%})"), width="stretch")
    st.caption(f"Cores: {m('grupo').funcao}. Posição: {m('pca').funcao}.")
with c2:
    st.plotly_chart(charts.dispersao(agr, "media_mensal", "cv", "nome_grupo", ordem, "Produção média × volatilidade",
                                     "Produção média mensal (escala log)", "Coeficiente de variação", log_x=True),
                    width="stretch")
    st.caption("Cada ponto é um município; as características são as de 2021–2024.")

st.markdown("#### Municípios de cada grupo")
abas = st.tabs([f"{g} ({(agr['nome_grupo'] == g).sum()})" for g in ordem])
for aba, g in zip(abas, ordem):
    with aba:
        t = agr[agr["nome_grupo"] == g].sort_values("media_mensal", ascending=False)
        st.dataframe(pd.DataFrame({"Município": t["nome"], "Produção média mensal": t["media_mensal"].map(fmt_compacto),
                                   "CV": t["cv"].map(fmt_num)}), hide_index=True, width="stretch", height=300)

with st.expander("Comparação com o agrupamento hierárquico (Ward)"):
    st.dataframe(pd.crosstab(agr["nome_grupo"], agr["grupo_hierarquico"].map(lambda g: f"Hierárquico {g + 1}")).reindex(ordem),
                 width="stretch")
    st.caption("Método de comparação: agrupamento hierárquico com ligação de Ward (scikit-learn AgglomerativeClustering). "
               "Os dois métodos concordam nos extremos e divergem no meio.")
st.info("Os grupos descrevem padrões de **registro** da produção, não a qualidade dos serviços de saúde.")
