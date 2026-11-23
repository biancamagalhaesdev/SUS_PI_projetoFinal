"""Leitura e validação dos arquivos de dados e resultados.

Nenhuma falha é escondida: se um arquivo faltar ou não tiver as colunas esperadas,
é levantado `ErroDados` com uma mensagem que explica o problema e como resolvê-lo.
"""
import json

import pandas as pd
import streamlit as st

from utils.config import ARQUIVOS, GEOJSON, JSONS, N_MUNICIPIOS_PI


class ErroDados(Exception):
    """Problema nos arquivos de dados (ausente, vazio ou com colunas faltando)."""


COMO_GERAR = {
    "producao": "Execute o apêndice de exportação do notebook e depois `python scripts/importar_resultados.py`.",
    "previsoes": "Execute o apêndice de exportação do notebook e depois `python scripts/importar_resultados.py`.",
    "metricas": "Execute o apêndice de exportação do notebook e depois `python scripts/importar_resultados.py`.",
    "agrupamentos": "Execute o apêndice de exportação do notebook e depois `python scripts/importar_resultados.py`.",
    "indicadores_alerta": "Execute `python scripts/gerar_alertas.py`.",
    "anomalias": "Execute `python scripts/gerar_alertas.py`.",
}


def ler_csv(nome: str) -> pd.DataFrame:
    caminho, colunas = ARQUIVOS[nome]
    if not caminho.exists():
        raise ErroDados(f"Arquivo não encontrado: `{caminho.relative_to(caminho.parents[2])}`. {COMO_GERAR[nome]}")
    df = pd.read_csv(caminho, dtype={"codigo_ibge": str})
    if df.empty:
        raise ErroDados(f"O arquivo `{caminho.name}` está vazio.")
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ErroDados(f"O arquivo `{caminho.name}` não tem as colunas obrigatórias: {', '.join(faltando)}.")
    if "competencia" in df.columns:
        df["competencia"] = pd.to_datetime(df["competencia"])
    if "codigo_ibge" in df.columns:
        df["codigo_ibge"] = df["codigo_ibge"].str.zfill(6)
    return df


def ler_json(nome: str) -> dict:
    caminho = JSONS[nome]
    if not caminho.exists():
        raise ErroDados(f"Arquivo não encontrado: `{caminho.name}`.")
    return json.loads(caminho.read_text(encoding="utf-8"))


def ler_geojson() -> dict:
    if not GEOJSON.exists():
        raise ErroDados("Malha municipal não encontrada (`data/processed/piaui_municipios.geojson`). "
                        "Execute `python scripts/baixar_malha.py`.")
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    n = len(geo.get("features", []))
    if n != N_MUNICIPIOS_PI:
        raise ErroDados(f"A malha municipal tem {n} municípios; o Piauí tem {N_MUNICIPIOS_PI}.")
    return geo


def catalogo_municipios(producao: pd.DataFrame, geo: dict) -> pd.DataFrame:
    """Tabela código ↔ nome oficial. A junção é feita pelo código IBGE, nunca pelo nome."""
    malha = pd.DataFrame([f["properties"] for f in geo["features"]])
    base = producao.drop_duplicates("codigo_ibge")[["codigo_ibge", "municipio"]]
    cat = base.merge(malha[["codigo_ibge", "codigo_ibge7", "nome"]], on="codigo_ibge", how="left")
    sem_malha = cat[cat["codigo_ibge7"].isna()]
    if not sem_malha.empty:
        raise ErroDados("Municípios da base sem correspondência na malha pelo código IBGE: "
                        + ", ".join(sem_malha["municipio"]))
    return cat.sort_values("nome").reset_index(drop=True)


# Versões com cache para a aplicação ------------------------------------------------
@st.cache_data(show_spinner="Carregando dados…")
def carregar(nome: str) -> pd.DataFrame:
    return ler_csv(nome)


@st.cache_data(show_spinner=False)
def carregar_json(nome: str) -> dict:
    return ler_json(nome)


@st.cache_data(show_spinner="Carregando a malha municipal…")
def carregar_geojson() -> dict:
    return ler_geojson()


@st.cache_data(show_spinner=False)
def carregar_catalogo() -> pd.DataFrame:
    return catalogo_municipios(carregar("producao"), carregar_geojson())


def exigir_dados(funcao, *args):
    """Executa um carregamento e, em caso de erro, mostra a mensagem e interrompe a página."""
    try:
        return funcao(*args)
    except ErroDados as e:
        st.error(f"**Erro ao carregar os dados.** {e}")
        st.stop()
