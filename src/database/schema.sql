-- Empresas cadastradas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    nome VARCHAR(200),
    cnpj VARCHAR(20),
    setor VARCHAR(100),
    subsetor VARCHAR(100),
    segmento VARCHAR(100),
    situacao VARCHAR(50),
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Cotacoes diarias
CREATE TABLE IF NOT EXISTS cotacoes (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    data DATE NOT NULL,
    abertura NUMERIC(15,2),
    maxima NUMERIC(15,2),
    minima NUMERIC(15,2),
    fechamento NUMERIC(15,2),
    volume BIGINT,
    variacao_pct NUMERIC(8,4),
    UNIQUE(empresa_id, data)
);

-- DRE - Demonstracao de Resultado
CREATE TABLE IF NOT EXISTS dre (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    periodo VARCHAR(10) NOT NULL,
    tipo VARCHAR(3) NOT NULL,
    receita_liquida NUMERIC(20,2),
    custo_produtos NUMERIC(20,2),
    lucro_bruto NUMERIC(20,2),
    despesas_operacionais NUMERIC(20,2),
    ebit NUMERIC(20,2),
    ebitda NUMERIC(20,2),
    resultado_financeiro NUMERIC(20,2),
    lucro_antes_ir NUMERIC(20,2),
    lucro_liquido NUMERIC(20,2),
    UNIQUE(empresa_id, periodo, tipo)
);

-- Balanco Patrimonial
CREATE TABLE IF NOT EXISTS balanco (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    periodo VARCHAR(10) NOT NULL,
    tipo VARCHAR(3) NOT NULL,
    ativo_total NUMERIC(20,2),
    ativo_circulante NUMERIC(20,2),
    ativo_nao_circulante NUMERIC(20,2),
    caixa_equivalentes NUMERIC(20,2),
    passivo_total NUMERIC(20,2),
    passivo_circulante NUMERIC(20,2),
    divida_bruta NUMERIC(20,2),
    divida_liquida NUMERIC(20,2),
    patrimonio_liquido NUMERIC(20,2),
    UNIQUE(empresa_id, periodo, tipo)
);

-- Fluxo de Caixa
CREATE TABLE IF NOT EXISTS fluxo_caixa (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    periodo VARCHAR(10) NOT NULL,
    tipo VARCHAR(3) NOT NULL,
    fcf_operacional NUMERIC(20,2),
    fcf_investimento NUMERIC(20,2),
    fcf_financiamento NUMERIC(20,2),
    capex NUMERIC(20,2),
    fcf_livre NUMERIC(20,2),
    UNIQUE(empresa_id, periodo, tipo)
);

-- Indicadores calculados
CREATE TABLE IF NOT EXISTS indicadores (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER REFERENCES empresas(id),
    data DATE NOT NULL,
    pl NUMERIC(10,2),
    pvp NUMERIC(10,2),
    ev_ebitda NUMERIC(10,2),
    psr NUMERIC(10,2),
    roe NUMERIC(8,4),
    roa NUMERIC(8,4),
    roic NUMERIC(8,4),
    margem_bruta NUMERIC(8,4),
    margem_ebitda NUMERIC(8,4),
    margem_liquida NUMERIC(8,4),
    divida_liq_ebitda NUMERIC(10,2),
    dividend_yield NUMERIC(8,4),
    payout NUMERIC(8,4),
    market_cap NUMERIC(20,2),
    enterprise_value NUMERIC(20,2),
    UNIQUE(empresa_id, data)
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_cotacoes_empresa_data ON cotacoes(empresa_id, data);
CREATE INDEX IF NOT EXISTS idx_indicadores_empresa_data ON indicadores(empresa_id, data);
CREATE INDEX IF NOT EXISTS idx_dre_empresa_periodo ON dre(empresa_id, periodo);
CREATE INDEX IF NOT EXISTS idx_empresas_ticker ON empresas(ticker);
