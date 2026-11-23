"""Descrição do projeto, métodos de cada indicador, fontes e limitações."""
import pandas as pd
import streamlit as st

from utils.config import LINKS
from utils.data_loader import ErroDados, carregar_json
from utils.indicators import fmt_num, fmt_pct
from utils.metodos import METODOS
from utils.ui import cabecalho

cabecalho("Sobre o projeto", "SUS Inteligente — Piauí: Plataforma de Inteligência Territorial da Produção Ambulatorial")


def json_opcional(nome):
    try:
        return carregar_json(nome)
    except ErroDados:
        return None


meta, lim, malha = json_opcional("metadados"), json_opcional("limites_alerta"), json_opcional("malha_fonte")

st.markdown("""
**Objetivo.** Apresentar os resultados de um projeto acadêmico de Aprendizado de Máquina sobre a produção ambulatorial
do SUS nos 224 municípios do Piauí: previsão da produção do mês seguinte (aprendizado supervisionado) e grupos de
municípios com comportamento semelhante (aprendizado não supervisionado), além de alertas estatísticos.

**Dados.** DATASUS — SIA/SUS, consulta no TabNet com Município na linha, Ano/mês de processamento na coluna e
Quantidade aprovada como conteúdo; jan/2021 a ago/2026. Limites municipais: malha oficial do IBGE (2024), associada
aos dados pelo código IBGE do município, nunca pelo nome.
""")

st.markdown("#### Indicadores e métodos")
st.dataframe(pd.DataFrame([{"Indicador": v.rotulo, "Como é calculado": v.calculo, "Função/algoritmo": v.funcao}
                           for v in METODOS.values()]), hide_index=True, width="stretch")
st.caption("A previsão e os grupos vêm do notebook do projeto; o site apenas lê os resultados exportados. "
           "Os alertas (incluindo o Isolation Forest) são calculados pelo site e não fazem parte do notebook.")

if lim:
    st.markdown("#### Limites dos alertas")
    st.markdown(
        f"Atenção: {lim['regra']['atencao']}; Alerta: {lim['regra']['alerta']}. Referência: {lim['regra']['referencia']}.\n\n"
        f"- Queda expressiva: Atenção ≤ {fmt_pct(lim['queda']['atencao'], 1, False)}; Alerta ≤ {fmt_pct(lim['queda']['alerta'], 1, False)}\n"
        f"- Instabilidade mensal: Atenção ≥ {fmt_num(lim['instabilidade']['atencao'])}; Alerta ≥ {fmt_num(lim['instabilidade']['alerta'])}\n"
        f"- Desvio em relação à previsão: Atenção ≥ {fmt_num(lim['desvio']['atencao'])}; Alerta ≥ {fmt_num(lim['desvio']['alerta'])}\n"
        f"- Anomalia (Isolation Forest): Atenção ≥ {fmt_num(lim['anomalia']['atencao'], 3)}; Alerta ≥ {fmt_num(lim['anomalia']['alerta'], 3)}")

st.markdown("""
#### Limitações
- Os dados representam a **produção registrada** (quantidade aprovada), e não a demanda da população, filas de espera
  ou a capacidade de atendimento.
- A série é organizada por mês de processamento e reflete também o fluxo administrativo de envio e aprovação.
- A base não traz procedimentos nem estabelecimentos.
- Em jun–ago/2026, dezenas de municípios aparecem com produção zero ao mesmo tempo e Teresina cai cerca de 40%.
- As previsões são de um mês à frente, sem intervalo de previsão, e erram mais nos municípios pequenos e instáveis.
- Os limites dos alertas são calculados com todos os municípios juntos; mudanças moderadas em municípios grandes e
  estáveis podem não ser sinalizadas.
- Alertas e grupos descrevem padrões estatísticos de registro, não a qualidade dos serviços de saúde.
""")

st.markdown("#### Links")
st.markdown(f"- Fonte dos dados: [DATASUS — TabNet]({LINKS['tabnet']})\n"
            f"- Malhas territoriais: [IBGE]({LINKS['ibge_malhas']}) · distribuição usada: [geobr (IPEA)]({LINKS['geobr']})\n"
            f"- Notebook do projeto: [{LINKS['notebook'] or 'a informar'}]({LINKS['notebook']})\n"
            f"- Repositório: [{LINKS['repositorio'] or 'a informar'}]({LINKS['repositorio']})")
if meta:
    st.caption(f"Resultados gerados em {meta['gerado_em']} · modelo de previsão: {meta['modelo_escolhido']} · "
               f"teste: {meta['periodo_teste'][0]} a {meta['periodo_teste'][1]}")
