"""Construção do mapa interativo do Piauí (Folium) e das escalas de cor dos indicadores."""
import copy
import html

import folium
import numpy as np
import pandas as pd
from branca.element import MacroElement, Template

from utils.config import COR, COR_NIVEL, NIVEIS, PALETA_GRUPOS

CENTRO_PI = (-7.3, -42.8)
SEQUENCIAL = ["#DCE9F5", "#A9C9E8", "#6FA4D6", "#3B7CC0", "#1F5FA8", "#0B2545"]
DIVERGENTE = ["#B2182B", "#E07B67", "#F4C6B5", "#EEEEEE", "#B6D3EA", "#5E9BD1", "#1F5FA8"]
LIMITES_VARIACAO = [-0.5, -0.25, -0.1, 0.1, 0.25, 0.5]


def colorir_quantis(valores: pd.Series, formatar, n: int = 6):
    """Classes por quantis (adequado a distribuições muito assimétricas)."""
    v = valores.dropna()
    if v.empty:
        return pd.Series(COR["sem_dado"], index=valores.index), [(COR["sem_dado"], "sem dado")]
    cortes = np.unique(np.quantile(v, np.linspace(0, 1, n + 1)))
    if len(cortes) < 2:
        cortes = np.array([v.min(), v.max() + 1e-9])
    paleta = SEQUENCIAL[-(len(cortes) - 1):] if len(cortes) - 1 <= len(SEQUENCIAL) else SEQUENCIAL
    classe = np.clip(np.searchsorted(cortes, valores, side="right") - 1, 0, len(cortes) - 2)
    cores = pd.Series([paleta[c] for c in classe], index=valores.index).where(valores.notna(), COR["sem_dado"])
    legenda = [(paleta[i], f"{formatar(cortes[i])} a {formatar(cortes[i + 1])}") for i in range(len(cortes) - 1)]
    if valores.isna().any():
        legenda.append((COR["sem_dado"], "sem dado"))
    return cores, legenda


def colorir_variacao(valores: pd.Series, formatar):
    """Escala divergente com limites fixos (−50%, −25%, −10%, +10%, +25%, +50%)."""
    classe = np.searchsorted(LIMITES_VARIACAO, valores.fillna(0), side="right")
    cores = pd.Series([DIVERGENTE[c] for c in classe], index=valores.index).where(valores.notna(), COR["sem_dado"])
    rotulos = ([f"abaixo de {formatar(LIMITES_VARIACAO[0])}"]
               + [f"{formatar(a)} a {formatar(b)}" for a, b in zip(LIMITES_VARIACAO[:-1], LIMITES_VARIACAO[1:])]
               + [f"acima de {formatar(LIMITES_VARIACAO[-1])}"])
    legenda = list(zip(DIVERGENTE, rotulos))
    if valores.isna().any():
        legenda.append((COR["sem_dado"], "sem dado"))
    return cores, legenda


def colorir_categorias(valores: pd.Series, ordem: list, cores_fixas: dict | None = None):
    mapa = cores_fixas or {c: PALETA_GRUPOS[i % len(PALETA_GRUPOS)] for i, c in enumerate(ordem)}
    cores = valores.map(mapa).fillna(COR["sem_dado"])
    legenda = [(mapa[c], c) for c in ordem]
    if valores.isna().any():
        legenda.append((COR["sem_dado"], "sem dado"))
    return cores, legenda


def colorir_niveis(niveis: pd.Series):
    return colorir_categorias(niveis, NIVEIS, COR_NIVEL)


class _Legenda(MacroElement):
    def __init__(self, titulo: str, itens: list, metodo: str = ""):
        super().__init__()
        linhas = "".join(
            f'<div style="display:flex;align-items:center;margin-top:3px;">'
            f'<span style="background:{c};width:14px;height:14px;display:inline-block;margin-right:6px;'
            f'border-radius:3px;border:1px solid #BBB;"></span>{html.escape(t)}</div>' for c, t in itens)
        self._template = Template(
            "{% macro html(this, kwargs) %}"
            '<div style="position:fixed;bottom:18px;left:12px;z-index:9999;background:rgba(255,255,255,.95);'
            'padding:8px 10px;border-radius:8px;border:1px solid #D0D6DE;font:12px sans-serif;color:#1B2A3A;'
            f'max-width:240px;"><b>{html.escape(titulo)}</b>'
            + (f'<div style="color:#1F5FA8;font-size:11px;margin-top:2px;">Método: {html.escape(metodo)}</div>' if metodo else "")
            + f'{linhas}</div>'
            "{% endmacro %}")


def construir_mapa(geo: dict, tabela: pd.DataFrame, titulo: str, legenda: list,
                   destaque: set | None = None, selecionado: str | None = None, enquadrar: bool = False,
                   altura_zoom: int = 6, metodo: str = "") -> folium.Map:
    """Mapa coroplético.

    `tabela` deve ter, por município (`codigo_ibge`), as colunas `cor` e `valor_fmt` (texto do tooltip).
    `destaque` recebe códigos de municípios em Alerta (contorno vermelho); `selecionado` recebe o
    município com contorno azul, e `enquadrar` aproxima o mapa dele.
    """
    destaque = destaque or set()
    info = tabela.set_index("codigo_ibge")
    g = copy.deepcopy(geo)
    for f in g["features"]:
        p = f["properties"]
        cod = p["codigo_ibge"]
        p["cor"] = info["cor"].get(cod, COR["sem_dado"])
        p["valor_fmt"] = info["valor_fmt"].get(cod, "sem dado")
        p["alerta"] = "sim" if cod in destaque else "não"
        p["selecionado"] = cod == selecionado

    def estilo(feature):
        p = feature["properties"]
        borda, peso = "#FFFFFF", 0.6
        if p["alerta"] == "sim":
            borda, peso = COR["vermelho"], 2.2
        if p["selecionado"]:
            borda, peso = COR["azul_escuro"], 3.2
        return {"fillColor": p["cor"], "color": borda, "weight": peso, "fillOpacity": 0.85}

    # Fundo neutro sem serviço externo; o mapa de ruas do OpenStreetMap fica disponível como camada opcional.
    m = folium.Map(location=CENTRO_PI, zoom_start=altura_zoom, tiles=None, control_scale=True, prefer_canvas=True)
    m.get_root().header.add_child(folium.Element("<style>.leaflet-container{background:#EEF2F7;}</style>"))
    folium.TileLayer("OpenStreetMap", name="Mapa de ruas (OpenStreetMap)", show=False, overlay=True,
                     control=True).add_to(m)
    campos, apelidos = ["nome", "valor_fmt"], ["Município", titulo]
    if destaque:
        campos.append("alerta")
        apelidos.append("Em alerta")
    folium.GeoJson(
        g, name=titulo, style_function=estilo,
        highlight_function=lambda f: {"weight": 3, "color": COR["azul_escuro"], "fillOpacity": 0.95},
        tooltip=folium.GeoJsonTooltip(fields=campos, aliases=apelidos, sticky=True),
    ).add_to(m)
    if selecionado and enquadrar:
        alvo = [f for f in g["features"] if f["properties"]["codigo_ibge"] == selecionado]
        if alvo:
            limites = folium.GeoJson(alvo[0]).get_bounds()
            m.fit_bounds(limites, padding=(60, 60), max_zoom=9)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    m.get_root().add_child(_Legenda(titulo, legenda, metodo))
    return m
