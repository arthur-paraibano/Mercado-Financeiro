from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Alerta:
    ticker: str
    tipo: str
    severidade: str       # 'CRITICO', 'ALTO', 'MEDIO', 'INFO'
    titulo: str
    descricao: str
    valor_detectado: Optional[float] = None
    threshold_usado: Optional[float] = None
    criado_em: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"[{self.severidade}] {self.ticker} - {self.titulo}"
