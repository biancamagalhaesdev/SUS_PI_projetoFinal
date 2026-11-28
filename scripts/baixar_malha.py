"""Baixa a malha municipal oficial do Piauí, valida e grava uma versão leve para o site.

Fontes, em ordem de tentativa:
  1. API de malhas territoriais do IBGE (servicodados.ibge.gov.br), com os nomes
     obtidos da API de localidades do IBGE.
  2. Malha municipal de 2024 do IBGE distribuída pelo pacote geobr (IPEA), nas
     releases públicas do GitHub.
  3. Arquivo já presente em data/raw/geo/ (cópia local da fonte 2).

Uso:  python scripts/baixar_malha.py
"""
import io
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from utils.config import GEOJSON, JSONS, N_MUNICIPIOS_PI, RAW  # noqa: E402

URL_IBGE_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/22"
                  "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria")
URL_IBGE_NOMES = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/22/municipios"
URL_GEOBR = "https://github.com/ipeaGIT/geobr/releases/download/v1.7.0/22municipality_2024_simplified.gpkg"
LOCAL_GEOBR = RAW / "geo" / "piaui_municipios_2024_geobr_simplificado.gpkg"
TOLERANCIA = 0.002   # graus (~200 m): simplificação para deixar o mapa leve


def baixar(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def da_api_ibge() -> gpd.GeoDataFrame:
    malha = gpd.read_file(io.BytesIO(baixar(URL_IBGE_MALHA)))
    nomes = pd.DataFrame(json.loads(baixar(URL_IBGE_NOMES)))[["id", "nome"]]
    malha["codigo_ibge7"] = malha["codarea"].astype(str)
    nomes["codigo_ibge7"] = nomes["id"].astype(str)
    return malha.merge(nomes[["codigo_ibge7", "nome"]], on="codigo_ibge7", how="left")


def do_geobr(caminho) -> gpd.GeoDataFrame:
    g = gpd.read_file(caminho)
    g["codigo_ibge7"] = g["code_muni"].astype("int64").astype(str)
    return g.rename(columns={"name_muni": "nome"})


def validar(g: gpd.GeoDataFrame) -> None:
    if len(g) != N_MUNICIPIOS_PI or g["codigo_ibge7"].nunique() != N_MUNICIPIOS_PI:
        raise ValueError(f"malha com {len(g)} municípios; esperado {N_MUNICIPIOS_PI}")
    if g["nome"].isna().any() or not g["codigo_ibge7"].str.fullmatch(r"22\d{5}").all():
        raise ValueError("malha com nomes ausentes ou códigos fora do padrão do Piauí")


def main() -> None:
    tentativas = [
        ("API de malhas do IBGE", lambda: da_api_ibge()),
        ("Malha municipal 2024 do IBGE via geobr (IPEA), GitHub", lambda: do_geobr(io.BytesIO(baixar(URL_GEOBR)))),
        ("Cópia local da malha 2024 do IBGE via geobr", lambda: do_geobr(LOCAL_GEOBR)),
    ]
    malha, fonte = None, None
    for nome, carregar in tentativas:
        try:
            g = carregar()
            validar(g)
            malha, fonte = g, nome
            print(f"[ok] {nome}")
            break
        except Exception as e:
            print(f"[falhou] {nome}: {e}")
    if malha is None:
        sys.exit("Nenhuma fonte da malha municipal funcionou. Verifique a conexão.")

    malha = malha.to_crs(4326)
    malha["geometry"] = malha.geometry.simplify(TOLERANCIA, preserve_topology=True)
    malha["codigo_ibge"] = malha["codigo_ibge7"].str[:6]
    malha = malha[["codigo_ibge", "codigo_ibge7", "nome", "geometry"]].sort_values("codigo_ibge")
    GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    malha.to_file(GEOJSON, driver="GeoJSON", COORDINATE_PRECISION=5)
    JSONS["malha_fonte"].write_text(json.dumps(
        {"fonte": fonte, "obtida_em": date.today().isoformat(), "simplificacao_graus": TOLERANCIA,
         "municipios": len(malha)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Malha gravada em {GEOJSON.relative_to(RAIZ)} ({GEOJSON.stat().st_size / 1024:.0f} KB), fonte: {fonte}")


if __name__ == "__main__":
    main()
