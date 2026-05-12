import streamlit as st

st.title("ℹ️ Sobre o Projeto")

st.markdown("""
## 📈 Mercado Financeiro BR

Dashboard completo de análise da bolsa brasileira (B3) com indicadores fundamentalistas,
análise técnica, recomendações automáticas e ferramentas educacionais para investidores
iniciantes.
""")

st.divider()

col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("### 👨‍💻 Desenvolvedor")
    st.markdown("**Arthur Paraibano**")
    st.markdown(
        "[🐙 GitHub](https://github.com/arthur-paraibano)  \n"
        "[📦 Repositório](https://github.com/arthur-paraibano/Mercado-Financeiro)  \n"
        "[🌐 App Online](https://mercado-financeiro-pb.streamlit.app)"
    )

with col2:
    st.markdown("### 🎯 Objetivo")
    st.markdown("""
Democratizar o acesso à análise da bolsa brasileira para investidores iniciantes,
com ferramentas claras, educacionais e baseadas em **dados públicos** (CVM, BCB, brapi.dev,
Fundamentus, Yahoo Finance).
    """)

st.divider()

st.markdown("### 🛠️ Tecnologias Utilizadas")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
**Backend**
- Python 3.12
- Pandas / NumPy
- SQLAlchemy
- Loguru
    """)
with col2:
    st.markdown("""
**Frontend**
- Streamlit 1.56
- Plotly
- Theme dark customizado
    """)
with col3:
    st.markdown("""
**Fontes de Dados**
- brapi.dev (cotações)
- Fundamentus (indicadores)
- BCB SGS (macro)
- CVM (DFP/ITR)
- Yahoo Finance
- InfoMoney, G1, Exame (RSS)
    """)

st.divider()

st.markdown("### ✨ Recursos do Dashboard")

st.markdown("""
- 🎓 **22 páginas** organizadas em 3 seções (Início, Fundamentalista, Análise Técnica)
- 🌱 **Modo Iniciante** com selo "Amigável para Iniciantes" nas recomendações
- 📊 **Recomendações automáticas** com scores de saúde, valuation, dividendos, crescimento e técnico
- 🆚 **Comparador "Qual é Melhor?"** entre 2 ou 3 ações
- 📓 **Diário do Investidor** com anotações pessoais e quiz educacional
- 🌡️ **Mapa de Calor** do mercado por setor
- ⭐ **Watchlist** com análise de diversificação e alertas de preço
- ⚖️ **Comparativo Ações vs Renda Fixa** (CDI, IPCA+, Ibovespa, Poupança)
- 💸 **Calendário de Dividendos** com timeline e calculadora de renda
- 🗓️ **Calendário Econômico Internacional** (Brasil, EUA, Zona Euro, China)
- 📰 **Painel de Notícias** com filtro por setor e análise de sentimento
- 📈 **Análise Técnica** com candlestick, RSI, MACD, Bollinger, SMA/EMA
""")

st.divider()

st.markdown("### ⚠️ Aviso Legal")
st.warning("""
Este projeto é **estritamente educacional**.

NÃO constitui recomendação profissional de investimento. Sempre faça sua própria análise
e considere consultar um profissional certificado (CFP®, CGA, analista CNPI) antes de
tomar decisões de investimento.

Os dados podem conter erros, atrasos ou indisponibilidades. O desenvolvedor não se
responsabiliza por perdas decorrentes do uso destas informações.
""")

st.divider()

st.markdown("### 🤝 Contribuições")
st.markdown("""
Sugestões, bugs e _pull requests_ são muito bem-vindos!

Acesse o [repositório no GitHub](https://github.com/arthur-paraibano/Mercado-Financeiro)
e abra uma issue ou PR.
""")

st.caption("© 2026 Arthur Paraibano · Projeto pessoal e educacional")
