"""Legenda de cada indicador: o que mede, como é calculado e qual função ou algoritmo o produz.

Todas as telas leem as legendas daqui, para que o mesmo indicador seja descrito da mesma forma
no mapa, nos cards, no painel do município e na página Sobre.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Metodo:
    rotulo: str      # nome exibido
    calculo: str     # como é calculado, em linguagem simples
    funcao: str      # função ou algoritmo que produz o valor


METODOS = {
    # Indicadores descritivos
    "producao_total": Metodo("Produção total", "Soma da quantidade aprovada nos meses do período",
                             "Soma — pandas DataFrame.sum"),
    "media_mensal": Metodo("Média mensal", "Média da quantidade aprovada por mês no período",
                           "Média aritmética — pandas DataFrame.mean"),
    "variacao": Metodo("Variação percentual", "Total do período ÷ total do período anterior de mesma duração − 1",
                       "Razão entre somas — pandas"),
    "cv": Metodo("Volatilidade (CV)", "Coeficiente de variação: desvio padrão ÷ média dos meses do período",
                 "Coeficiente de variação — pandas std ÷ mean"),
    "tendencia": Metodo("Tendência", "Mediana dos últimos 12 meses ÷ mediana dos 12 anteriores − 1 (limiar de ±10%)",
                        "Razão entre medianas — pandas median"),
    # Aprendizado de máquina (resultados do notebook)
    "previsao": Metodo("Previsão do próximo mês", "Previsão de um mês à frente com o modelo escolhido na validação",
                       "Random Forest — scikit-learn RandomForestRegressor"),
    "grupo": Metodo("Grupo territorial", "Agrupamento das 7 características de 2021–2024, padronizadas",
                    "K-Means (k = 3) — scikit-learn KMeans"),
    "silhueta": Metodo("Silhueta", "Mede a separação entre os grupos, de −1 a 1 (maior é melhor)",
                       "Coeficiente de silhueta — scikit-learn silhouette_score"),
    "pca": Metodo("Variância explicada", "Parte da variação das 7 características resumida em 2 eixos",
                  "Análise de componentes principais — scikit-learn PCA"),
    # Alertas (calculados pelo site)
    "alerta": Metodo("Classificação de alerta",
                     "Critério mais grave entre queda, instabilidade, desvio da previsão e anomalia; "
                     "Atenção e Alerta nos percentis 95 e 99 do período de referência",
                     "Regras por percentis + Isolation Forest — scikit-learn IsolationForest"),
    "queda": Metodo("Queda expressiva", "Média dos últimos 3 meses ÷ mediana dos 12 meses anteriores",
                    "Médias e medianas móveis — pandas rolling"),
    "instabilidade": Metodo("Instabilidade mensal", "Coeficiente de variação dos últimos 12 meses",
                            "Desvio e média móveis — pandas rolling"),
    "desvio": Metodo("Desvio em relação à previsão", "|log(1 + real) − log(1 + previsto)|, com as previsões do Random Forest",
                     "Diferença em log — NumPy log1p"),
    "anomalia": Metodo("Anomalia", "Escore de anomalia das variações do município em relação ao mês anterior, "
                                   "ao mesmo mês do ano anterior e à mediana dos 12 meses anteriores",
                       "Isolation Forest — scikit-learn IsolationForest"),
    # Métricas de erro
    "mae": Metodo("MAE", "Erro absoluto médio, em procedimentos", "scikit-learn mean_absolute_error"),
    "mape": Metodo("MAPE", "Erro percentual médio; exclui os meses com produção zero", "Cálculo em NumPy"),
    # Métodos de previsão comparados
    "Naive sazonal": Metodo("Naive sazonal", "Repete a produção do mesmo mês do ano anterior",
                            "Regra de referência (baseline)"),
    "Regressão Linear": Metodo("Regressão Linear", "Soma ponderada dos atributos, com pesos ajustados aos dados",
                               "scikit-learn LinearRegression"),
    "Random Forest": Metodo("Random Forest", "Média de 100 árvores de decisão treinadas em amostras dos dados",
                            "scikit-learn RandomForestRegressor"),
    "Rede neural MLP": Metodo("Rede neural MLP", "Duas camadas de neurônios que ajustam seus pesos para reduzir o erro",
                              "scikit-learn MLPRegressor"),
}

INDICADOR_PARA_NIVEL = {"queda": "nivel_queda", "instabilidade": "nivel_instabilidade",
                        "desvio": "nivel_desvio", "anomalia": "nivel_anomalia"}
NOME_EVENTO = {"queda": "Queda expressiva", "instabilidade": "Instabilidade mensal",
               "desvio": "Desvio em relação à previsão", "anomalia": "Anomalia (Isolation Forest)"}


def m(chave: str) -> Metodo:
    return METODOS[chave]


def legenda(chave: str) -> str:
    """Texto curto para mostrar abaixo de um valor."""
    return METODOS[chave].funcao
