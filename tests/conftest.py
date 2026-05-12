import sys
from pathlib import Path

# Garantir que imports do projeto funcionam nos testes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
