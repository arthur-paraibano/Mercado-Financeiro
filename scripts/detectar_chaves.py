"""Detecta chaves de dict acentuadas que provavelmente quebrarao acesso."""
import re
import unicodedata
from pathlib import Path

KEYS_SEM_ACENTO = {
    "saude", "tecnico", "tecnica", "preco", "cotacao", "variacao", "media", "minima", "maxima",
    "opcao", "opcoes", "periodo", "historico", "descricao", "situacao", "criterio", "criterios",
    "simulacao", "comecar", "comeca", "avaliacao", "concentracao", "diversificacao",
    "projecao", "classificacao", "noticia", "noticias", "recomendacao", "recomendacoes",
    "acao", "acoes", "visao", "configuracao", "atualizacao", "distribuicao", "reducao",
    "expansao", "divida", "dividas", "inflacao", "alocacao", "integracao", "credito",
    "ja", "nao", "voce", "sao", "estao", "so", "util", "ultima", "ultimo", "proximo", "proxima",
    "metrica", "metricas", "grafico", "graficos", "rapido", "rapida", "calculo", "calculos",
    "serie", "series", "mes", "concluido", "eh", "dica", "saude", "tecnico", "comeca",
}


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


PADRAO_GET = re.compile(r"\.get\((['\"])([^'\"]+)\1")
PADRAO_INDEX = re.compile(r"\[(['\"])([^'\"]+)\1\]")
PADRAO_EQUALS = re.compile(r"==\s*(['\"])([^'\"]+)\1")  # comparações com strings (ex: tipo == "saúde")

problemas = []
for path in Path("dashboard").rglob("*.py"):
    txt = path.read_text(encoding="utf-8")
    for i, line in enumerate(txt.split("\n"), 1):
        # Pular comentarios
        if line.lstrip().startswith("#"):
            continue
        for pat in (PADRAO_GET, PADRAO_INDEX, PADRAO_EQUALS):
            for m in pat.finditer(line):
                key = m.group(2)
                sem = strip_accents(key).lower()
                if sem != key.lower() and sem in KEYS_SEM_ACENTO:
                    problemas.append((path, i, line.strip(), key, sem))

if not problemas:
    print("Nenhum problema encontrado.")
else:
    print(f"{len(problemas)} ocorrências:")
    for p, i, l, k, s in problemas:
        print(f"{p}:{i}: '{k}' -> '{s}'")
        print(f"  {l[:120]}")
