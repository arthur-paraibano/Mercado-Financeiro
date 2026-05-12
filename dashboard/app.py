import streamlit as st

from dashboard.components.i18n import aplicar_traducoes_streamlit

st.set_page_config(
    page_title="Mercado Financeiro BR",
    page_icon="📈",
    layout="wide",
)

# Traduz strings nativas do Streamlit ("View X more", "View less", etc.)
aplicar_traducoes_streamlit()

# --- Navegação com seções ---
comecar_aqui = st.Page("pages/comecar_aqui.py", title="Começar Aqui", icon="🎓", default=True)
fundamentalista = st.Page("pages/recomendacoes.py", title="Recomendações", icon="🎯")
empresa = st.Page("pages/empresa.py", title="Empresa", icon="🏢")
visao_geral = st.Page("pages/visao_geral.py", title="Visão Geral", icon="📊")
macro = st.Page("pages/macro.py", title="Indicadores Macro", icon="🏦")
comparacao = st.Page("pages/comparacao_setorial.py", title="Comparação Setorial", icon="⚖️")
alertas = st.Page("pages/alertas.py", title="Alertas", icon="🚨")
ranking = st.Page("pages/ranking.py", title="Ranking", icon="🏆")
screening = st.Page("pages/screening.py", title="Filtro de Ações", icon="🔍")
fundos = st.Page("pages/fundos.py", title="Fundos (Smart Money)", icon="💰")
governanca = st.Page("pages/governanca.py", title="Governança", icon="🛡️")
mapa_calor = st.Page("pages/mapa_calor.py", title="Mapa de Calor", icon="🌡️")
watchlist = st.Page("pages/watchlist.py", title="Watchlist", icon="⭐")
comparativo_rf = st.Page("pages/comparativo_rf.py", title="Ações vs Renda Fixa", icon="⚖️")
dividendos = st.Page("pages/dividendos.py", title="Calendário de Dividendos", icon="💸")
noticias = st.Page("pages/noticias.py", title="Notícias", icon="📰")
calendario_eco = st.Page("pages/calendario_economico.py", title="Calendário Econômico", icon="🗓️")
qual_e_melhor = st.Page("pages/qual_e_melhor.py", title="Qual é Melhor?", icon="🆚")
diario = st.Page("pages/diario.py", title="Diário do Investidor", icon="📓")

tecnica_analise = st.Page("pages/tecnica_analise.py", title="Análise Técnica", icon="📈")
tecnica_sinais = st.Page("pages/tecnica_sinais.py", title="Scanner de Sinais", icon="📡")
tecnica_comparativo = st.Page("pages/tecnica_comparativo.py", title="Comparativo", icon="🔀")

sobre = st.Page("pages/sobre.py", title="Sobre", icon="ℹ️")

pg = st.navigation({
    "Início": [comecar_aqui, diario],
    "Fundamentalista": [
        fundamentalista, qual_e_melhor, empresa, visao_geral, macro, comparacao,
        alertas, ranking, screening, fundos, governanca,
        mapa_calor, watchlist, comparativo_rf, dividendos, noticias, calendario_eco,
    ],
    "Análise Técnica": [
        tecnica_analise, tecnica_sinais, tecnica_comparativo,
    ],
    "Outros": [sobre],
})

pg.run()

# --- Rodapé global na sidebar (aparece em todas as páginas) ---
with st.sidebar:
    st.markdown("---")
    st.caption(
        "👨‍💻 Desenvolvido por **Arthur Paraibano**  \n"
        "[GitHub](https://github.com/arthur-paraibano) · "
        "[Repositório](https://github.com/arthur-paraibano/Mercado-Financeiro)"
    )
    st.caption("⚠️ Conteúdo educacional. Não constitui recomendação de investimento.")
