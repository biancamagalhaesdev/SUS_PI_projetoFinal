"""Calcula os indicadores de alerta e grava os resultados usados pelo site.

Entradas: data/processed/producao_municipal.csv e data/results/previsoes.csv
Saídas:   data/results/indicadores_alerta.csv, anomalias.csv e limites_alerta.json

Uso:  python scripts/gerar_alertas.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from utils.alerts import calcular, eventos  # noqa: E402
from utils.config import ARQUIVOS, JSONS  # noqa: E402
from utils.data_loader import ErroDados, catalogo_municipios, ler_csv, ler_geojson  # noqa: E402

COLUNAS_SAIDA = ["codigo_ibge", "competencia", "producao", "queda_razao", "nivel_queda", "cv_12m",
                 "nivel_instabilidade", "modelo", "real", "previsto", "desvio_log", "nivel_desvio",
                 "var_mediana12", "var_mes_anterior", "var_ano_anterior", "escore_anomalia",
                 "nivel_anomalia", "nivel_geral"]


def main() -> None:
    try:
        producao, previsoes = ler_csv("producao"), ler_csv("previsoes")
        cat = catalogo_municipios(producao, ler_geojson())
    except ErroDados as e:
        sys.exit(f"[erro] {e}")
    ind, limites = calcular(producao, previsoes)
    ev = eventos(ind, limites, cat.set_index("codigo_ibge")["nome"])

    saida = ind[COLUNAS_SAIDA].copy()
    saida["competencia"] = saida["competencia"].dt.strftime("%Y-%m-01")
    saida.to_csv(ARQUIVOS["indicadores_alerta"][0], index=False)
    ev_out = ev.copy()
    ev_out["competencia"] = ev_out["competencia"].dt.strftime("%Y-%m-01")
    ev_out.to_csv(ARQUIVOS["anomalias"][0], index=False)
    JSONS["limites_alerta"].write_text(json.dumps(limites, ensure_ascii=False, indent=1), encoding="utf-8")

    ultimo = ind["competencia"].max()
    atual = ind[ind["competencia"] == ultimo]["nivel_geral"].value_counts()
    print(f"Indicadores: {len(saida)} linhas | eventos: {len(ev)}")
    print("Eventos por indicador e classificação:")
    print(ev.groupby(["indicador", "classificacao"]).size().unstack(fill_value=0).to_string())
    print(f"Situação em {ultimo:%Y-%m}: {atual.to_dict()}")
    print("Limites:", {k: {kk: round(vv, 4) for kk, vv in v.items() if isinstance(vv, float)}
                       for k, v in limites.items() if k != "regra"})


if __name__ == "__main__":
    main()
