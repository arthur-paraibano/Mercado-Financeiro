"""Detecta identificadores Python acentuados (provaveis bugs)."""
import re
import sys
from pathlib import Path

# Forcar UTF-8 no stdout (Windows console default e cp1252)
sys.stdout.reconfigure(encoding="utf-8")

# Palavras acentuadas que provavelmente sao variaveis Python (sufixo _ e prefixo)
SUSPEITAS = [
    "última", "último", "últimas", "últimos", "gráfico", "período", "média",
    "mínima", "máxima", "mínimo", "máximo", "série", "séries", "índice",
    "preço", "cotação", "variação", "ações", "ação", "país", "países",
    "cálculo", "mês", "rápido", "útil", "técnico", "técnica", "análise",
    "saúde", "opção", "opções", "próximo", "próxima", "já", "não", "são",
    "você", "estão", "só", "décimo", "sessão", "área", "férias", "histórico",
    "média", "índice", "número", "último", "três", "também",
]

# Padrao 1: identificador dentro de {} de f-string ex: {última['close']}
RE_F_STRING_VAR = re.compile(r"\{[^{}]*?\b(" + "|".join(re.escape(s) for s in SUSPEITAS) + r")\b[^{}]*?\}")
# Padrao 2: identificador no inicio de uma linha (atribuicao) ex: última = df.iloc[-1]
RE_ASSIGN = re.compile(r"^\s*(" + "|".join(re.escape(s) for s in SUSPEITAS) + r")\s*=\s*[^=]")
# Padrao 3: identificador como argumento ou comparacao ex: foo(última) ou == última
RE_REF = re.compile(r"(?:\(|,|==|!=)\s*(" + "|".join(re.escape(s) for s in SUSPEITAS) + r")\b")

problemas = set()
for path in sorted(Path("dashboard").rglob("*.py")):
    txt = path.read_text(encoding="utf-8")
    for i, line in enumerate(txt.split("\n"), 1):
        for pat in (RE_F_STRING_VAR, RE_ASSIGN, RE_REF):
            for m in pat.finditer(line):
                problemas.add((str(path), i, line.strip()[:140], m.group(1)))

if not problemas:
    print("Nenhum problema encontrado.")
else:
    for p, i, l, v in sorted(problemas):
        print(f"{p}:{i}: [{v}] -> {l}")
    print(f"\nTotal: {len(problemas)} ocorrências")
