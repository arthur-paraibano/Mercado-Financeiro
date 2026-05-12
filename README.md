# 📈 Mercado Financeiro BR

> **🌐 App online:** https://mercado-financeiro-pb.streamlit.app
>
> **👨‍💻 Desenvolvedor:** Arthur Paraibano · [GitHub @arthur-paraibano](https://github.com/arthur-paraibano)

Dashboard completo de análise da bolsa brasileira (B3) com indicadores fundamentalistas, análise técnica, recomendações automáticas e ferramentas educacionais para investidores iniciantes.

## ✨ Recursos

### 🎓 Para Iniciantes
- **Começar Aqui** — wizard de onboarding com perfil de risco e carteira sugerida
- **Diário do Investidor** — anotações e quiz educacional
- **Selo "Amigável para Iniciantes"** em ações com fundamentos sólidos

### 📊 Análise Fundamentalista
- Recomendações automáticas (Compra Forte, Compra, Neutro, Cautela, Evitar)
- Comparador "Qual é Melhor?" lado a lado
- Análise por empresa (P/L, P/VP, ROE, ROIC, DY, margens, dívida)
- Ranking, screening (filtro), comparação setorial
- Smart Money (fundos institucionais), governança
- Mapa de calor do mercado
- Watchlist personalizada com alertas de preço e análise de diversificação

### 📈 Análise Técnica
- Gráficos candlestick com indicadores (SMA, EMA, RSI, MACD, Bollinger)
- Scanner de sinais técnicos
- Comparativo entre ações

### 🌐 Macro e Mercado
- Indicadores macro (Selic, IPCA, CDI, câmbio)
- Calendário econômico internacional (Brasil, EUA, Zona Euro, China)
- Calendário de dividendos
- Comparativo "Ações vs Renda Fixa" (CDI, IPCA+, Ibovespa, Poupança)
- Painel de notícias por setor (InfoMoney, G1, Exame, Valor)

## 🚀 Deploy no Streamlit Cloud (gratuito)

### Passo a passo

1. **Faça fork ou clone deste repositório** no seu GitHub.
2. **Acesse:** https://share.streamlit.io
3. **Login com GitHub.**
4. Clique em **"New app"** e selecione:
   - Repository: `seu-usuario/Mercado-Financeiro`
   - Branch: `main`
   - Main file path: `dashboard/app.py`
5. Em **"Advanced settings" → "Secrets"**, adicione:
   ```toml
   BRAPI_TOKEN = "seu_token_aqui"
   ```
   Obtenha um token gratuito em https://brapi.dev (necessário para cotações).
6. Clique em **Deploy!** Em ~2 minutos seu app está no ar.

## 💻 Rodar Localmente

```bash
# Criar ambiente virtual (Python 3.12+)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Criar .env com o token brapi
echo "BRAPI_TOKEN=seu_token_aqui" > .env

# Rodar
streamlit run dashboard/app.py
```

Acesse http://localhost:8501

## 🧪 Testes

```bash
pytest tests/ -v
```

## 📁 Estrutura

```
.
├── config/              # Configurações e settings
├── dashboard/           # Aplicação Streamlit
│   ├── app.py           # Entry point com navegação
│   ├── components/      # Helpers compartilhados
│   └── pages/           # 22 páginas do dashboard
├── src/                 # Backend
│   ├── collectors/      # APIs (brapi, BCB, CVM, Fundamentus, IBGE)
│   ├── processors/      # Indicadores, scores, recomendações
│   ├── alerts/          # Engine de alertas
│   ├── models/          # Modelos de dados
│   └── database/        # PostgreSQL (opcional, uso local)
├── tests/               # 36 testes pytest
└── scripts/             # Utilitários
```

## 🛠️ Tecnologias

- **Python 3.12** + **Streamlit 1.56**
- **Pandas**, **NumPy**, **Plotly**
- **brapi.dev**, **Fundamentus**, **BCB SGS**, **CVM**, **Yahoo Finance**
- **feedparser** (RSS de notícias)

## ⚠️ Aviso Legal

Este projeto é **educacional**. NÃO constitui recomendação profissional de investimento. Sempre faça sua própria análise e considere consultar um profissional certificado antes de investir.

## 📜 Licença

Uso pessoal e educacional.

## 👨‍💻 Autor

**Arthur Paraibano**

- 🐙 GitHub: [@arthur-paraibano](https://github.com/arthur-paraibano)
- 📦 Repositório: [Mercado-Financeiro](https://github.com/arthur-paraibano/Mercado-Financeiro)

Sinta-se à vontade para abrir _issues_, _pull requests_ ou sugestões!
