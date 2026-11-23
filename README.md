# SUS Inteligente — Piauí

**Plataforma de Inteligência Territorial da Produção Ambulatorial.**

Aplicação web que apresenta, de forma acessível, os resultados de um projeto acadêmico de Aprendizado de Máquina
sobre a produção ambulatorial do SUS nos 224 municípios do Piauí, de janeiro de 2021 a agosto de 2026. O site exibe um
mapa interativo, indicadores municipais, previsões, grupos de municípios e alertas, sempre com o método de cada número.

> **Importante.** Os dados representam a **produção ambulatorial registrada** no SIA/SUS (quantidade aprovada, por mês
> de processamento). Eles não equivalem à demanda da população, a filas de espera nem à capacidade de atendimento.
> Os alertas indicam alterações estatísticas na produção registrada, não deficiências de atendimento.

## Páginas

| Página | Conteúdo |
|---|---|
| Mapa (inicial) | Indicadores gerais do estado e mapa dos municípios com 7 camadas (produção total, média mensal, variação, volatilidade, previsão do próximo mês, grupo e classificação de alerta), pesquisa por nome, destaque dos municípios em alerta e painel com os detalhes do município clicado |
| Município | Indicadores, resumo analítico gerado por regras, produção registrada × prevista, erro de cada método de previsão e alertas do município |
| Grupos | Grupos do K-Means, gráfico da PCA, características e municípios de cada grupo e comparação com o agrupamento hierárquico |
| Sobre | Objetivo, dados, tabela de indicadores e métodos, limites dos alertas, limitações e links |

**Cada indicador mostra o método que o produziu.** No mapa, a faixa abaixo dos controles e a legenda do mapa trazem o
cálculo e a função ou algoritmo da camada escolhida; nos cards e no painel, cada valor tem uma linha "Método". As
legendas ficam centralizadas em `utils/metodos.py`, e a página Sobre reúne todas em uma tabela.

## Tecnologias

Python 3.12, Streamlit (interface e navegação), Folium e streamlit-folium (mapa), Plotly (gráficos), Pandas e NumPy
(dados), scikit-learn (Isolation Forest) e GeoPandas (preparação da malha municipal). Versões fixadas em
`requirements.txt`.

## Estrutura

```text
sus-inteligente/
├── app.py                     # ponto de entrada: navegação (no topo) e identidade visual
├── pages/                     # as 4 páginas: Mapa, Município, Grupos e Sobre
├── utils/
│   ├── config.py              # caminhos, esquemas dos arquivos, cores e links
│   ├── metodos.py             # legenda de cada indicador: cálculo e função/algoritmo
│   ├── data_loader.py         # leitura e validação dos dados (erros visíveis)
│   ├── contexto.py            # dados combinados e seleção de município entre páginas
│   ├── indicators.py          # indicadores, formatação e resumo analítico
│   ├── alerts.py              # critérios de alerta e Isolation Forest
│   ├── maps.py                # mapa e escalas de cor
│   ├── charts.py              # gráficos
│   └── ui.py                  # cards, cabeçalhos e estilo
├── scripts/
│   ├── baixar_malha.py        # baixa e prepara a malha municipal oficial
│   ├── importar_resultados.py # importa os resultados exportados pelo notebook
│   └── gerar_alertas.py       # calcula os alertas
├── data/
│   ├── raw/                   # planilha original do DATASUS e malha bruta
│   ├── processed/             # produção em formato longo e malha simplificada
│   └── results/               # resultados do notebook e alertas
├── tests/                     # testes automáticos (pytest)
├── .streamlit/config.toml     # tema
├── requirements.txt
└── requirements-dev.txt
```

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. O repositório já inclui todos os dados e resultados necessários; nenhum
passo adicional é obrigatório para executar.

## Como inserir ou atualizar os dados

O site **não treina modelos**: ele lê os resultados exportados pelo notebook do projeto. Para atualizar:

1. Execute o notebook do projeto até o fim. O apêndice "Exportação dos resultados para o site" grava a pasta
   `resultados_site/` e o pacote `resultados_site.zip` (no Colab, o download começa automaticamente).
2. Importe os resultados (os esquemas são validados durante a importação):
   ```bash
   python scripts/importar_resultados.py caminho/para/resultados_site.zip
   ```
3. Recalcule os alertas:
   ```bash
   python scripts/gerar_alertas.py
   ```
4. Se precisar baixar a malha municipal novamente:
   ```bash
   python scripts/baixar_malha.py
   ```

Se algum arquivo faltar ou estiver com colunas erradas, a página correspondente mostra uma mensagem de erro que diz
qual arquivo está com problema e como gerá-lo. O site não usa dados demonstrativos.

### Esquema dos arquivos

| Arquivo | Origem | Colunas |
|---|---|---|
| `data/processed/producao_municipal.csv` | notebook | `codigo_ibge` (6 dígitos), `municipio`, `competencia` (AAAA-MM-01), `producao` |
| `data/results/previsoes.csv` | notebook | `codigo_ibge`, `municipio`, `competencia`, `modelo`, `periodo` (validação, teste ou próximo mês), `real`, `previsto`, `escolhido` |
| `data/results/metricas_modelos.csv` | notebook | `modelo`, `periodo`, `conjunto_atributos`, `hiperparametros`, `MAE`, `RMSE`, `MAPE`, `R2`, `meses_com_zero`, `n`, `escolhido` |
| `data/results/agrupamentos.csv` | notebook | `codigo_ibge`, `municipio`, as 7 características do Conjunto B, `grupo_kmeans`, `nome_grupo`, `grupo_hierarquico`, `pca1`, `pca2` |
| `data/results/agrupamento_info.json` | notebook | número de grupos, ordem dos nomes, silhueta e inércia por k, variância e cargas da PCA |
| `data/results/metadados.json` | notebook | períodos, modelo escolhido, mês previsto e versões |
| `data/results/indicadores_alerta.csv` | `gerar_alertas.py` | valores e níveis dos 4 indicadores por município e mês, e a classificação geral |
| `data/results/anomalias.csv` | `gerar_alertas.py` | `codigo_ibge`, `municipio`, `competencia`, `indicador`, `valor`, `intensidade`, `classificacao`, `justificativa` |
| `data/results/limites_alerta.json` | `gerar_alertas.py` | limites de cada indicador e a regra usada |
| `data/processed/piaui_municipios.geojson` | `baixar_malha.py` | polígonos com `codigo_ibge` (6 dígitos), `codigo_ibge7` e `nome` |

## Dados geográficos

A malha municipal é a **malha oficial do IBGE (2024)**, distribuída pelo pacote geobr (IPEA). O script
`baixar_malha.py` tenta primeiro a API de malhas do próprio IBGE e, se ela não estiver acessível, usa a distribuição do
geobr; em ambos os casos confere se há exatamente 224 municípios. A fonte usada fica registrada em
`data/processed/malha_fonte.json`.

A base do DATASUS usa o código IBGE de 6 dígitos e a malha, o de 7 dígitos (com o dígito verificador). A junção é feita
pelos 6 primeiros dígitos do código oficial, **nunca pelo nome**; um teste automático confere os 224 pares.

## Critérios dos alertas

Regra única para os quatro indicadores: o valor de cada município em cada mês é comparado com a distribuição do mesmo
indicador em um período de referência. **Atenção**: mais extremo que 95% dos casos de referência; **Alerta**: mais
extremo que 99%; **Estável**: demais casos. A classificação geral é a mais grave entre os indicadores.

| Indicador | Medida | Referência |
|---|---|---|
| Queda expressiva | Média dos últimos 3 meses ÷ mediana dos 12 meses anteriores | 2021–2024 |
| Instabilidade mensal | Coeficiente de variação dos últimos 12 meses | 2021–2024 |
| Desvio em relação à previsão | \|log(1 + real) − log(1 + previsto)\| do modelo escolhido no notebook | validação de 2025 |
| Anomalia (Isolation Forest) | Escore de anomalia a partir das variações em relação ao mês anterior, ao mesmo mês do ano anterior e à mediana dos 12 meses anteriores | 2022–2024 |

Os limites calculados ficam em `limites_alerta.json` e são exibidos na página Sobre. O Isolation Forest e
os alertas são calculados pelo site e não fazem parte das análises do notebook.

**Limitações dos critérios:**
- Os limites são calculados com todos os municípios juntos, então mudanças relativas moderadas em municípios grandes e
  estáveis podem não ser classificadas como atípicas.
- Um pico isolado mantém o indicador de instabilidade elevado por até 12 meses.
- O desvio em relação à previsão só existe de jan/2025 a ago/2026.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes conferem a integridade dos dados, a junção geográfica, os indicadores, os critérios e a linguagem dos alertas,
e executam todas as páginas e suas interações principais com o `AppTest` do Streamlit.

## Publicação (Streamlit Community Cloud)

1. Envie esta pasta para um repositório **público** no GitHub.
2. Em https://share.streamlit.io, escolha **Create app**, selecione o repositório e informe `app.py` como arquivo
   principal.
3. Em *Advanced settings*, escolha Python 3.12. O serviço instala as dependências do `requirements.txt`.
4. Preencha os links do notebook e do repositório em `utils/config.py` (`LINKS`) para que apareçam na página Sobre.

## Limitações gerais

- A base não traz procedimentos nem estabelecimentos; não há filtros ou análises por grupo de procedimento.
- As previsões são de um mês à frente, sem intervalo de previsão.
- Os meses de jun–ago/2026 foram atípicos (dezenas de municípios com produção zero ao mesmo tempo e queda de cerca de
  40% em Teresina); a causa não pode ser identificada com estes dados.
- Alertas e agrupamentos descrevem padrões estatísticos de registro, não a qualidade dos serviços de saúde.

## Fontes

- Produção ambulatorial: Ministério da Saúde, DATASUS — SIA/SUS (TabNet): https://datasus.saude.gov.br/informacoes-de-saude-tabnet/
- Malha municipal: IBGE, via geobr (IPEA): https://github.com/ipeaGIT/geobr
