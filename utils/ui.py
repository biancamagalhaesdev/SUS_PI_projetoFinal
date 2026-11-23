"""Componentes visuais compartilhados: estilo, cabeçalho, cards e avisos."""
import html

import streamlit as st

from utils.config import COR, COR_NIVEL

CSS = f"""
<style>
.block-container {{padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1400px;}}
h1, h2, h3 {{color: {COR['azul_escuro']};}}
.cabecalho {{border-left: 6px solid {COR['azul']}; padding: .2rem 0 .2rem 1rem; margin-bottom: 1.2rem;}}
.cabecalho .titulo {{font-size: 1.75rem; font-weight: 700; color: {COR['azul_escuro']}; line-height: 1.2;}}
.cabecalho .subtitulo {{font-size: .98rem; color: #4A5A6E; margin-top: .25rem;}}
.card {{background: #FFFFFF; border: 1px solid #E1E6EE; border-radius: 12px; padding: .9rem 1rem;
        height: 100%; box-shadow: 0 1px 2px rgba(11,37,69,.04);}}
.card .rotulo {{font-size: .8rem; color: #5B6B7F; text-transform: uppercase; letter-spacing: .03em;}}
.card .valor {{font-size: 1.55rem; font-weight: 700; color: {COR['azul_escuro']}; margin-top: .2rem;
               overflow-wrap: anywhere;}}
.card .detalhe {{font-size: .82rem; color: #5B6B7F; margin-top: .15rem;}}
.metodo {{font-size: .74rem; color: {COR['azul']}; margin-top: .35rem; line-height: 1.25;}}
.metodo b {{font-weight: 600;}}
.selo {{display: inline-block; padding: .1rem .55rem; border-radius: 999px; font-size: .8rem;
        font-weight: 600; color: #FFFFFF;}}
.painel {{background: #FFFFFF; border: 1px solid #E1E6EE; border-radius: 12px; padding: 1rem 1.1rem;}}
.marca {{font-weight: 700; color: {COR['azul_escuro']}; font-size: 1.05rem; line-height: 1.25;}}
.marca span {{display: block; font-weight: 400; font-size: .78rem; color: #5B6B7F;}}
@media (max-width: 640px) {{
  .cabecalho .titulo {{font-size: 1.35rem;}}
  .card .valor {{font-size: 1.25rem;}}
}}
</style>
"""

AVISO_INTERPRETACAO = ("Os dados representam a **produção ambulatorial registrada** no SIA/SUS (quantidade aprovada, "
                       "por mês de processamento). Eles não equivalem à demanda da população, a filas de espera "
                       "nem à capacidade de atendimento.")


def configurar_estilo() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(titulo: str, subtitulo: str = "") -> None:
    sub = f'<div class="subtitulo">{html.escape(subtitulo)}</div>' if subtitulo else ""
    st.markdown(f'<div class="cabecalho"><div class="titulo">{html.escape(titulo)}</div>{sub}</div>',
                unsafe_allow_html=True)


def card(rotulo: str, valor: str, detalhe: str = "", metodo: str = "") -> None:
    """Card com valor, detalhe e a função ou algoritmo que produziu o valor."""
    det = f'<div class="detalhe">{html.escape(detalhe)}</div>' if detalhe else ""
    met = f'<div class="metodo"><b>Método:</b> {html.escape(metodo)}</div>' if metodo else ""
    st.markdown(f'<div class="card"><div class="rotulo">{html.escape(rotulo)}</div>'
                f'<div class="valor">{html.escape(valor)}</div>{det}{met}</div>', unsafe_allow_html=True)


def legenda_metodo(calculo: str, funcao: str) -> None:
    """Faixa com o cálculo e a função ou algoritmo do indicador selecionado."""
    st.markdown(f'<div class="metodo" style="font-size:.85rem;margin:.2rem 0 .6rem 0;">'
                f'<b>Como é calculado:</b> {html.escape(calculo)} &nbsp;·&nbsp; '
                f'<b>Função/algoritmo:</b> {html.escape(funcao)}</div>', unsafe_allow_html=True)


def linha_de_cards(itens: list, por_linha: int = 3) -> None:
    """Cards em grade; no celular as colunas se empilham automaticamente."""
    for i in range(0, len(itens), por_linha):
        colunas = st.columns(por_linha)
        for col, item in zip(colunas, itens[i:i + por_linha]):
            with col:
                card(*item)
        st.write("")


def selo_nivel(nivel: str) -> str:
    cor = COR_NIVEL.get(nivel, COR["cinza"])
    return f'<span class="selo" style="background:{cor}">{html.escape(nivel)}</span>'


def aviso_interpretacao() -> None:
    st.caption(AVISO_INTERPRETACAO)


def barra_lateral(metadados: dict | None = None) -> None:
    with st.sidebar:
        st.markdown('<div class="marca">SUS Inteligente — Piauí'
                    '<span>Plataforma de Inteligência Territorial da Produção Ambulatorial</span></div>',
                    unsafe_allow_html=True)
        if metadados:
            ini, fim = metadados["periodo_dados"]
            st.caption(f"Dados: DATASUS — SIA/SUS · {ini.replace('-', '/')} a {fim.replace('-', '/')}")
