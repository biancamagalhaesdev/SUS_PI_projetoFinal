"""Configuração central da aplicação: caminhos, esquemas dos arquivos, cores e links."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "data"
RAW = DADOS / "raw"
PROCESSED = DADOS / "processed"
RESULTS = DADOS / "results"

# Arquivos esperados e colunas obrigatórias de cada um.
ARQUIVOS = {
    "producao": (PROCESSED / "producao_municipal.csv",
                 ["codigo_ibge", "municipio", "competencia", "producao"]),
    "previsoes": (RESULTS / "previsoes.csv",
                  ["codigo_ibge", "municipio", "competencia", "modelo", "periodo", "real", "previsto", "escolhido"]),
    "metricas": (RESULTS / "metricas_modelos.csv",
                 ["modelo", "periodo", "conjunto_atributos", "hiperparametros", "MAE", "RMSE", "MAPE", "R2", "n", "escolhido"]),
    "agrupamentos": (RESULTS / "agrupamentos.csv",
                     ["codigo_ibge", "municipio", "media_mensal", "desvio_padrao", "cv", "crescimento",
                      "producao_maxima", "producao_minima", "amplitude_sazonal",
                      "grupo_kmeans", "nome_grupo", "grupo_hierarquico", "pca1", "pca2"]),
    "indicadores_alerta": (RESULTS / "indicadores_alerta.csv",
                           ["codigo_ibge", "competencia", "queda_razao", "nivel_queda", "cv_12m", "nivel_instabilidade",
                            "desvio_log", "nivel_desvio", "escore_anomalia", "nivel_anomalia", "nivel_geral"]),
    "anomalias": (RESULTS / "anomalias.csv",
                  ["codigo_ibge", "municipio", "competencia", "indicador", "valor", "intensidade",
                   "classificacao", "justificativa"]),
}
JSONS = {
    "agrupamento_info": RESULTS / "agrupamento_info.json",
    "metadados": RESULTS / "metadados.json",
    "limites_alerta": RESULTS / "limites_alerta.json",
    "malha_fonte": PROCESSED / "malha_fonte.json",
}
GEOJSON = PROCESSED / "piaui_municipios.geojson"
N_MUNICIPIOS_PI = 224

# Identidade visual
COR = {
    "azul_escuro": "#0B2545",
    "azul": "#1F5FA8",
    "azul_claro": "#8DB3E2",
    "cinza_claro": "#F4F6F9",
    "cinza": "#8A94A6",
    "sem_dado": "#D9DDE3",
    "verde": "#2E8B57",
    "amarelo": "#E0A800",
    "vermelho": "#C0392B",
}
NIVEIS = ["Estável", "Atenção", "Alerta"]
COR_NIVEL = {"Estável": COR["verde"], "Atenção": COR["amarelo"], "Alerta": COR["vermelho"]}
PALETA_GRUPOS = ["#1F5FA8", "#2E8B57", "#D9822B", "#7B4EA3", "#C0392B", "#5B6B7F"]

MESES_NOME = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
              7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# Links (preencha os do projeto antes de publicar)
LINKS = {
    "tabnet": "https://datasus.saude.gov.br/informacoes-de-saude-tabnet/",
    "ibge_malhas": "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html",
    "geobr": "https://github.com/ipeaGIT/geobr",
    "notebook": "https://colab.research.google.com/drive/1hTscUxpXlogzbHGFjUDRCnI6uTWfMnAf?usp=sharing",
    "repositorio": "https://github.com/biancamagalhaesdev/SUS_PI",
}

# Páginas (caminhos usados na navegação entre páginas)
PAGINA = {
    "mapa": "pages/1_Mapa.py",
    "municipio": "pages/2_Municipio.py",
    "grupos": "pages/3_Grupos.py",
    "sobre": "pages/4_Sobre.py",
}
