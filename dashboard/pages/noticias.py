import html
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import streamlit as st


def limpar_html(texto: str) -> str:
    """Remove tags HTML e decodifica entidades. Evita erros de React no Streamlit."""
    if not texto:
        return ""
    # Remove tags HTML
    sem_tags = re.sub(r"<[^>]+>", "", texto)
    # Decodifica entidades HTML (&amp; -> &, &nbsp; -> espaço, etc.)
    decodificado = html.unescape(sem_tags)
    # Normaliza espaços/quebras
    return re.sub(r"\s+", " ", decodificado).strip()

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.collectors.b3_collector import SETORES_B3  # noqa: E402

st.title("📰 Notícias do Mercado")
st.caption("Notícias financeiras em tempo real por setor e empresa.")

# --- Feeds RSS ---
FEEDS = {
    "InfoMoney": "https://www.infomoney.com.br/feed/",
    "G1 Economia": "https://g1.globo.com/rss/g1/economia/",
    "Exame": "https://exame.com/feed/",
    "Valor Econômico": "https://valor.globo.com/financas/rss.atom/",
}

# Mapeamento setor -> palavras-chave para filtrar noticias
KEYWORDS_SETOR = {
    "Petróleo e Gas": ["petróleo", "petrobras", "petr4", "prio3", "gas", "pre-sal", "combustivel", "brent"],
    "Mineração e Siderurgia": ["vale", "mineração", "minério", "aço", "siderurgia", "csna3", "ggbr4", "usim5"],
    "Financeiro": ["banco", "itau", "bradesco", "santander", "crédito", "financeiro", "juros", "selic", "itub4"],
    "Energia Elétrica": ["energia", "elétrica", "eletrobras", "aneel", "tarifa", "hidrelétrica", "solar", "eolica"],
    "Varejo": ["varejo", "magazineluiza", "magalu", "lojas", "e-commerce", "comercio", "consumo"],
    "Agronegocio": ["agro", "soja", "milho", "exportacao", "embrapa", "jbs", "brfs3", "carne"],
    "Saúde": ["saúde", "hospital", "medicina", "farmacia", "plano de saúde", "sus", "rdor3", "hapvida"],
    "Telecomunicacoes": ["telecomunicacoes", "telefônica", "vivo", "tim", "claro", "anatel", "fibra", "5g"],
    "Tecnologia": ["tecnologia", "totvs", "startup", "software", "digital", "inteligencia artificial", "ti"],
    "Transporte e Logistica": ["logistica", "frete", "aeroporto", "ferrovia", "ccro3", "azul", "embraer"],
}

# Palavras-chave de sentimento
POSITIVOS = ["alta", "lucro", "crescimento", "recorde", "ganho", "expansão", "aprovado", "positivo", "subiu", "atingiu"]
NEGATIVOS = ["queda", "prejuizo", "redução", "perda", "crise", "risco", "negativo", "caiu", "fraude", "processo"]


def detectar_sentimento(texto: str) -> str:
    texto_lower = texto.lower()
    pos = sum(1 for p in POSITIVOS if p in texto_lower)
    neg = sum(1 for n in NEGATIVOS if n in texto_lower)
    if pos > neg:
        return "positivo"
    elif neg > pos:
        return "negativo"
    return "neutro"


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_noticias_cache(feeds_tuple: tuple) -> list[dict]:
    noticias = []
    feeds = dict(feeds_tuple)
    for fonte, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:25]:
                titulo = limpar_html(getattr(entry, "title", "") or "")
                link = getattr(entry, "link", "") or ""
                summary = limpar_html(getattr(entry, "summary", "") or "")

                # Parsear data
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass

                if titulo and link:
                    noticias.append({
                        "titulo": titulo,
                        "link": link,
                        "resumo": summary[:300] if summary else "",
                        "fonte": fonte,
                        "data": published,
                        "texto_busca": (titulo + " " + summary).lower(),
                    })
        except Exception:
            pass

    # Ordenar por data (mais recentes primeiro), sem data vai para o final
    noticias.sort(key=lambda x: x["data"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return noticias


# --- Configurações ---
with st.expander("⚙️ Configurações", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Fontes**")
        fontes_sel = st.multiselect(
            "Selecione as fontes:",
            list(FEEDS.keys()),
            default=list(FEEDS.keys()),
            label_visibility="collapsed",
        )
        st.markdown("**Filtro por tema**")
        modo_filtro = st.radio(
            "Filtrar por:",
            ["Todos", "Setor", "Palavra-chave"],
            horizontal=True,
            label_visibility="collapsed",
        )
        busca_personalizada = ""
        setor_sel = None
        if modo_filtro == "Setor":
            setor_sel = st.selectbox("Setor:", list(KEYWORDS_SETOR.keys()))
        elif modo_filtro == "Palavra-chave":
            busca_personalizada = st.text_input(
                "Buscar:", placeholder="Ex: Petrobras, selic, dividendos"
            )

    with col2:
        st.markdown("**Período**")
        periodo_h = st.selectbox(
            "Publicado nas últimas:",
            ["24 horas", "48 horas", "7 dias", "Todos"],
            index=2,
            label_visibility="collapsed",
        )
        st.markdown("**Sentimento**")
        sentimento_filtro = st.multiselect(
            "Sentimento:",
            ["positivo", "negativo", "neutro"],
            default=["positivo", "negativo", "neutro"],
            label_visibility="collapsed",
        )

horas_map = {"24 horas": 24, "48 horas": 48, "7 dias": 168, "Todos": 99999}
horas_max = horas_map[periodo_h]

# --- Carregar noticias ---
with st.spinner("Carregando notícias..."):
    feeds_filtrados = {k: v for k, v in FEEDS.items() if k in fontes_sel}
    if not feeds_filtrados:
        st.warning("Selecione pelo menos uma fonte.")
        st.stop()

    todas_noticias = buscar_noticias_cache(tuple(feeds_filtrados.items()))

# --- Aplicar filtros ---
noticias_filtradas = []
agora = datetime.now(timezone.utc)

for n in todas_noticias:
    # Filtro de tempo
    if n["data"] is not None:
        delta_h = (agora - n["data"]).total_seconds() / 3600
        if delta_h > horas_max:
            continue

    # Filtro por setor
    if modo_filtro == "Setor" and setor_sel:
        keywords = KEYWORDS_SETOR.get(setor_sel, [])
        if not any(kw in n["texto_busca"] for kw in keywords):
            continue

    # Filtro por palavra-chave personalizada
    if modo_filtro == "Palavra-chave" and busca_personalizada:
        if busca_personalizada.lower() not in n["texto_busca"]:
            continue

    # Detectar sentimento
    sentimento = detectar_sentimento(n["titulo"] + " " + n["resumo"])
    if sentimento not in sentimento_filtro:
        continue

    n["sentimento"] = sentimento
    noticias_filtradas.append(n)

# --- Exibir ---
st.subheader(f"{len(noticias_filtradas)} notícias encontradas")

if not noticias_filtradas:
    st.info("Nenhuma notícia encontrada com os filtros atuais. Tente ampliar o período ou mudar os filtros.")
    st.stop()

# Metricas rapidas
col1, col2, col3 = st.columns(3)
col1.metric("Positivas 🟢", sum(1 for n in noticias_filtradas if n["sentimento"] == "positivo"))
col2.metric("Negativas 🔴", sum(1 for n in noticias_filtradas if n["sentimento"] == "negativo"))
col3.metric("Neutras ⚪", sum(1 for n in noticias_filtradas if n["sentimento"] == "neutro"))

st.divider()

# Cards de noticias
ICONE_SENTIMENTO = {"positivo": "🟢", "negativo": "🔴", "neutro": "⚪"}
COR_BORDA = {"positivo": "#2ca02c", "negativo": "#d62728", "neutro": "#7f7f7f"}

for n in noticias_filtradas[:50]:
    icone = ICONE_SENTIMENTO.get(n["sentimento"], "⚪")
    data_str = n["data"].strftime("%d/%m/%Y %H:%M") if n["data"] else "Data desconhecida"

    titulo_seguro = limpar_html(n["titulo"])
    resumo_seguro = limpar_html(n["resumo"])
    if len(resumo_seguro) > 220:
        resumo_seguro = resumo_seguro[:220] + "..."

    with st.container(border=True):
        st.caption(f"{icone} **{n['fonte']}**  ·  {data_str}")
        st.markdown(f"**[{titulo_seguro}]({n['link']})**")
        if resumo_seguro:
            st.caption(resumo_seguro)

if len(noticias_filtradas) > 50:
    st.info(f"Mostrando 50 de {len(noticias_filtradas)} notícias. Refine os filtros para ver resultados mais especificos.")

st.caption("Fontes: InfoMoney, G1 Economia, Exame, Valor Econômico | Cache: 30 minutos")
