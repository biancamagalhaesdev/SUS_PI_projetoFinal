"""Dados combinados usados por várias páginas e a seleção de município compartilhada entre elas."""
import pandas as pd
import streamlit as st

from utils.data_loader import carregar, carregar_catalogo
from utils.indicators import matriz

CHAVE_MUNICIPIO = "municipio_sel"     # chave não ligada a widget: sobrevive à troca de página


@st.cache_data(show_spinner=False)
def base():
    """(produção com nome oficial, catálogo de municípios, matriz município × mês)."""
    prod = carregar("producao")
    cat = carregar_catalogo()
    nomes = cat.set_index("codigo_ibge")["nome"]
    prod = prod.assign(nome=prod["codigo_ibge"].map(nomes))
    return prod, cat, matriz(prod)


def nomes_municipios(cat: pd.DataFrame) -> pd.Series:
    return cat.set_index("codigo_ibge")["nome"]


def municipio_atual():
    return st.session_state.get(CHAVE_MUNICIPIO)


def definir_municipio(codigo: str | None) -> None:
    st.session_state[CHAVE_MUNICIPIO] = codigo


def seletor_municipio(cat: pd.DataFrame, chave: str, rotulo: str = "Município") -> str:
    """Caixa de seleção que começa no município escolhido em outra página e atualiza a escolha."""
    codigos = cat["codigo_ibge"].tolist()
    nomes = nomes_municipios(cat)
    atual = municipio_atual()
    indice = codigos.index(atual) if atual in codigos else codigos.index(cat.loc[cat["nome"] == "Teresina", "codigo_ibge"].iloc[0])

    def sincronizar():
        definir_municipio(st.session_state[chave])

    escolha = st.selectbox(rotulo, codigos, index=indice, format_func=lambda c: nomes.get(c, c),
                           key=chave, on_change=sincronizar)
    definir_municipio(escolha)
    return escolha


def abrir_analise(codigo: str, pagina: str) -> None:
    definir_municipio(codigo)
    st.switch_page(pagina)
