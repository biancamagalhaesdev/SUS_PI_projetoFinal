"""Importa os resultados exportados pelo apêndice do notebook para as pastas do site.

Uso:
  python scripts/importar_resultados.py caminho/para/resultados_site.zip
  python scripts/importar_resultados.py caminho/para/pasta_resultados_site

Depois da importação, execute `python scripts/gerar_alertas.py`.
"""
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from utils.config import PROCESSED, RESULTS  # noqa: E402
from utils.data_loader import ErroDados, ler_csv, ler_json  # noqa: E402

DESTINOS = {
    "producao_municipal.csv": PROCESSED,
    "previsoes.csv": RESULTS,
    "metricas_modelos.csv": RESULTS,
    "agrupamentos.csv": RESULTS,
    "agrupamento_info.json": RESULTS,
    "metadados.json": RESULTS,
}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    origem = Path(sys.argv[1])
    if not origem.exists():
        sys.exit(f"Não encontrado: {origem}")
    with tempfile.TemporaryDirectory() as tmp:
        if origem.suffix == ".zip":
            zipfile.ZipFile(origem).extractall(tmp)
            origem = Path(tmp)
        faltando = [n for n in DESTINOS if not (origem / n).exists()]
        if faltando:
            sys.exit(f"Arquivos ausentes no pacote: {', '.join(faltando)}")
        for nome, destino in DESTINOS.items():
            destino.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem / nome, destino / nome)
            print(f"[copiado] {nome} -> {destino.relative_to(RAIZ)}")
    try:                                   # valida esquemas com as mesmas regras do site
        for nome in ["producao", "previsoes", "metricas", "agrupamentos"]:
            df = ler_csv(nome)
            print(f"[válido] {nome}: {len(df)} linhas")
        for nome in ["agrupamento_info", "metadados"]:
            ler_json(nome)
    except ErroDados as e:
        sys.exit(f"[erro] {e}")
    print("Importação concluída. Próximo passo: python scripts/gerar_alertas.py")


if __name__ == "__main__":
    main()
