"""Configuração dos testes: torna o pacote `utils` importável a partir da raiz do projeto."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
