import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

st.title("🗓️ Calendário Econômico")
st.caption("Principais eventos econômicos internacionais e impacto esperado no mercado.")

# ========================================
# Base de eventos 2026
# (COPOM: https://www.bcb.gov.br/controleinflacao/reunioescopom)
# (FOMC: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)
# ========================================
EVENTOS = [
    # ---- BRASIL ----
    {"data": "2026-01-28", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "12,25%", "previsao": "13,00%"},
    {"data": "2026-02-11", "país": "BR", "bandeira": "🇧🇷", "evento": "IPCA — Janeiro", "categoria": "Inflação", "impacto": "alto", "anterior": "0,52%", "previsao": "0,48%"},
    {"data": "2026-03-11", "país": "BR", "bandeira": "🇧🇷", "evento": "IPCA — Fevereiro", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-03-18", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-04-09", "país": "BR", "bandeira": "🇧🇷", "evento": "IPCA — Marco", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-05-06", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-05-12", "país": "BR", "bandeira": "🇧🇷", "evento": "IPCA — Abril", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-06-10", "país": "BR", "bandeira": "🇧🇷", "evento": "IPCA — Maio", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-06-17", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-07-09", "país": "BR", "bandeira": "🇧🇷", "evento": "IPCA — Junho", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-07-29", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-09-09", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-10-28", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-12-09", "país": "BR", "bandeira": "🇧🇷", "evento": "COPOM — Decisão Selic", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    # PIB Brasil (divulgado trimestralmente)
    {"data": "2026-03-06", "país": "BR", "bandeira": "🇧🇷", "evento": "PIB — T4 2025", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-06-05", "país": "BR", "bandeira": "🇧🇷", "evento": "PIB — T1 2026", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-09-04", "país": "BR", "bandeira": "🇧🇷", "evento": "PIB — T2 2026", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},

    # ---- EUA ----
    {"data": "2026-01-28", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "4,25-4,50%", "previsao": "4,25-4,50%"},
    {"data": "2026-02-12", "país": "US", "bandeira": "🇺🇸", "evento": "CPI — Janeiro", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-03-18", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-04-10", "país": "US", "bandeira": "🇺🇸", "evento": "CPI — Marco", "categoria": "Inflação", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-05-06", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-06-10", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-07-29", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-09-16", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-11-04", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-12-16", "país": "US", "bandeira": "🇺🇸", "evento": "FOMC — Decisão Fed Funds", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    # NFP (Payroll) - primeira sexta de cada mes
    {"data": "2026-02-06", "país": "US", "bandeira": "🇺🇸", "evento": "Payroll (NFP) — Janeiro", "categoria": "Emprego", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-03-06", "país": "US", "bandeira": "🇺🇸", "evento": "Payroll (NFP) — Fevereiro", "categoria": "Emprego", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-04-03", "país": "US", "bandeira": "🇺🇸", "evento": "Payroll (NFP) — Marco", "categoria": "Emprego", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-05-08", "país": "US", "bandeira": "🇺🇸", "evento": "Payroll (NFP) — Abril", "categoria": "Emprego", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-06-05", "país": "US", "bandeira": "🇺🇸", "evento": "Payroll (NFP) — Maio", "categoria": "Emprego", "impacto": "alto", "anterior": "—", "previsao": "—"},
    # PIB EUA
    {"data": "2026-01-29", "país": "US", "bandeira": "🇺🇸", "evento": "PIB EUA — T4 2025 (1a leitura)", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-04-29", "país": "US", "bandeira": "🇺🇸", "evento": "PIB EUA — T1 2026 (1a leitura)", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},

    # ---- ZONA EURO ----
    {"data": "2026-01-30", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "3,00%", "previsao": "2,75%"},
    {"data": "2026-03-06", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-04-17", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-06-05", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-07-23", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-09-10", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-10-22", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-12-03", "país": "EU", "bandeira": "🇪🇺", "evento": "BCE — Decisão Taxa de Juro", "categoria": "Juros", "impacto": "alto", "anterior": "—", "previsao": "—"},
    # CPI Zona Euro (flash mensal)
    {"data": "2026-02-04", "país": "EU", "bandeira": "🇪🇺", "evento": "CPI Zona Euro — Janeiro (Flash)", "categoria": "Inflação", "impacto": "medio", "anterior": "—", "previsao": "—"},
    {"data": "2026-03-04", "país": "EU", "bandeira": "🇪🇺", "evento": "CPI Zona Euro — Fevereiro (Flash)", "categoria": "Inflação", "impacto": "medio", "anterior": "—", "previsao": "—"},

    # ---- CHINA ----
    {"data": "2026-01-17", "país": "CN", "bandeira": "🇨🇳", "evento": "PIB China — T4 2025", "categoria": "PIB", "impacto": "alto", "anterior": "4,6%", "previsao": "5,0%"},
    {"data": "2026-02-14", "país": "CN", "bandeira": "🇨🇳", "evento": "IPC China — Janeiro", "categoria": "Inflação", "impacto": "medio", "anterior": "—", "previsao": "—"},
    {"data": "2026-03-09", "país": "CN", "bandeira": "🇨🇳", "evento": "IPC China — Fevereiro", "categoria": "Inflação", "impacto": "medio", "anterior": "—", "previsao": "—"},
    {"data": "2026-04-16", "país": "CN", "bandeira": "🇨🇳", "evento": "PIB China — T1 2026", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-07-15", "país": "CN", "bandeira": "🇨🇳", "evento": "PIB China — T2 2026", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},
    {"data": "2026-10-16", "país": "CN", "bandeira": "🇨🇳", "evento": "PIB China — T3 2026", "categoria": "PIB", "impacto": "alto", "anterior": "—", "previsao": "—"},
    # PMI China (NBS - ultimo dia util do mes)
    {"data": "2026-01-31", "país": "CN", "bandeira": "🇨🇳", "evento": "PMI Industrial China — Janeiro", "categoria": "PMI", "impacto": "medio", "anterior": "—", "previsao": "—"},
    {"data": "2026-02-28", "país": "CN", "bandeira": "🇨🇳", "evento": "PMI Industrial China — Fevereiro", "categoria": "PMI", "impacto": "medio", "anterior": "—", "previsao": "—"},
    {"data": "2026-03-31", "país": "CN", "bandeira": "🇨🇳", "evento": "PMI Industrial China — Marco", "categoria": "PMI", "impacto": "medio", "anterior": "—", "previsao": "—"},
]

# ========================================
# Configurações
# ========================================
with st.expander("⚙️ Configurações", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        paises_disponiveis = {"Todos": None, "Brasil 🇧🇷": "BR", "EUA 🇺🇸": "US", "Zona Euro 🇪🇺": "EU", "China 🇨🇳": "CN"}
        pais_sel = st.selectbox("País:", list(paises_disponiveis.keys()))

        categorias_disp = sorted(set(e["categoria"] for e in EVENTOS))
        categorias_sel = st.multiselect("Categorias:", categorias_disp, default=categorias_disp)

        impacto_sel = st.multiselect("Impacto:", ["alto", "medio", "baixo"], default=["alto", "medio"])

    with col2:
        meses_frente = st.slider("Próximos (meses):", 1, 12, 3)
        mostrar_passados = st.checkbox("Incluir eventos passados", value=True)
        meses_passados_cal = st.slider("Histórico (meses):", 1, 6, 1, disabled=not mostrar_passados)

# ========================================
# Processar dados
# ========================================
df = pd.DataFrame(EVENTOS)
df["data"] = pd.to_datetime(df["data"])
df = df.sort_values("data").reset_index(drop=True)

hoje = pd.Timestamp(date.today())
data_inicio = hoje - pd.DateOffset(months=meses_passados_cal if mostrar_passados else 0)
data_fim = hoje + pd.DateOffset(months=meses_frente)

# Aplicar filtros
mask = (df["data"] >= data_inicio) & (df["data"] <= data_fim)
if not mostrar_passados:
    mask = mask & (df["data"] >= hoje)
if paises_disponiveis[pais_sel]:
    mask = mask & (df["país"] == paises_disponiveis[pais_sel])
if categorias_sel:
    mask = mask & (df["categoria"].isin(categorias_sel))
if impacto_sel:
    mask = mask & (df["impacto"].isin(impacto_sel))

df_filtrado = df[mask].copy()

# ========================================
# Alertas: proximos 7 dias
# ========================================
df_proximos7 = df_filtrado[
    (df_filtrado["data"] >= hoje) &
    (df_filtrado["data"] <= hoje + pd.DateOffset(days=7)) &
    (df_filtrado["impacto"] == "alto")
]

if not df_proximos7.empty:
    st.warning(f"**{len(df_proximos7)} evento(s) de alto impacto nos próximos 7 dias!**")
    for _, ev in df_proximos7.iterrows():
        dias_restantes = (ev["data"] - hoje).days
        label = "Hoje" if dias_restantes == 0 else f"Em {dias_restantes} dia(s)"
        st.markdown(f"- {ev['bandeira']} **{ev['evento']}** — {ev['data'].strftime('%d/%m/%Y')} ({label})")
    st.divider()

# ========================================
# Metricas
# ========================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total no Período", len(df_filtrado))
col2.metric("Alto Impacto", len(df_filtrado[df_filtrado["impacto"] == "alto"]))
col3.metric("Próximos 30d", len(df_filtrado[(df_filtrado["data"] >= hoje) & (df_filtrado["data"] <= hoje + pd.DateOffset(days=30))]))
col4.metric("Passados", len(df_filtrado[df_filtrado["data"] < hoje]))

st.divider()

# ========================================
# Timeline visual
# ========================================
st.subheader("Timeline de Eventos")

COR_IMPACTO = {"alto": "#d62728", "medio": "#ff7f0e", "baixo": "#2ca02c"}
COR_PAIS = {"BR": "#009c3b", "US": "#3c3b6e", "EU": "#003399", "CN": "#de2910"}
TAMANHO_IMPACTO = {"alto": 18, "medio": 12, "baixo": 8}

fig = px.scatter(
    df_filtrado,
    x="data",
    y="país",
    color="impacto",
    symbol="categoria",
    size=[TAMANHO_IMPACTO.get(i, 10) for i in df_filtrado["impacto"]],
    size_max=20,
    color_discrete_map=COR_IMPACTO,
    hover_name="evento",
    hover_data={"país": False, "bandeira": True, "categoria": True, "anterior": True, "previsao": True, "data": True},
    title="Eventos Econômicos por País e Impacto",
    labels={"país": "País", "data": "Data", "impacto": "Impacto", "categoria": "Categoria"},
    category_orders={"país": ["BR", "US", "EU", "CN"]},
)

hoje_str = hoje.strftime("%Y-%m-%d")
fig.add_shape(type="line", x0=hoje_str, x1=hoje_str, y0=0, y1=1,
              yref="paper", line=dict(dash="dash", color="yellow", width=1.5), opacity=0.7)
fig.add_annotation(x=hoje_str, y=1, yref="paper", text="Hoje",
                   showarrow=False, yanchor="bottom", font=dict(color="yellow", size=11))

fig.update_layout(height=350, hovermode="closest", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, width="stretch")

st.divider()

# ========================================
# Tabela detalhada
# ========================================
st.subheader("Lista de Eventos")

# Adicionar coluna de status
def status_evento(data_ev):
    if data_ev < hoje:
        return "✅ Concluído"
    elif data_ev == hoje:
        return "🔴 Hoje"
    elif data_ev <= hoje + pd.DateOffset(days=7):
        return "⚠️ Esta semana"
    elif data_ev <= hoje + pd.DateOffset(days=30):
        return "📅 Próximo mes"
    return "🔮 Futuro"

df_filtrado = df_filtrado.copy()
df_filtrado["Status"] = df_filtrado["data"].apply(status_evento)
df_filtrado["Data"] = df_filtrado["data"].dt.strftime("%d/%m/%Y")
df_filtrado["Dias"] = (df_filtrado["data"] - hoje).dt.days

cols_show = ["Status", "Data", "Dias", "bandeira", "evento", "categoria", "impacto", "anterior", "previsao"]
df_show = df_filtrado[cols_show].rename(columns={
    "bandeira": "País",
    "evento": "Evento",
    "categoria": "Categoria",
    "impacto": "Impacto",
    "anterior": "Anterior",
    "previsao": "Previsao",
    "Dias": "Dias p/ Evento",
})

def cor_impacto_cel(val):
    if val == "alto":
        return "color: #d62728; font-weight: bold"
    elif val == "medio":
        return "color: #ff7f0e"
    return "color: #2ca02c"

styled = df_show.style.map(cor_impacto_cel, subset=["Impacto"])
st.dataframe(styled, width="stretch", hide_index=True, height=500)

# ========================================
# Legenda
# ========================================
st.divider()
st.markdown("""
**Legenda de Impacto:**
- 🔴 **Alto** — Pode causar volatilidade significativa no mercado (decisões de juros, PIB, payroll)
- 🟠 **Medio** — Relevante para setores especificos ou tendencias de medio prazo
- 🟢 **Baixo** — Indicadores secundarios com impacto limitado

**Fontes:**
- COPOM: bcb.gov.br | FOMC: federalreserve.gov | BCE: ecb.europa.eu
- Datas sujeitas a alteracao pelos bancos centrais
""")

st.caption("Eventos curados manualmente | Atualizado para 2026 | Datas aproximadas para eventos recorrentes")
