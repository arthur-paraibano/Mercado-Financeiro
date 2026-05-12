from typing import List

from src.models.alert import Alerta


class CrossAnalyzer:
    """Motor de cruzamento de dados para gerar alertas e insights."""

    # --- Thresholds configuraveis ---
    DIVIDA_EBITDA_CRITICO = 5.0
    DIVIDA_EBITDA_ALTO = 3.5
    MARGEM_LIQUIDA_CRITICA = -5.0
    COBERTURA_JUROS_MINIMA = 1.5

    # ================================================================
    # CRUZAMENTO 1: Saude Financeira
    # ================================================================
    def analisar_saude_financeira(
        self, ticker: str, dados: dict
    ) -> List[Alerta]:
        """
        Detecta problemas de saude financeira.
        dados: dict normalizado do Fundamentus.
        """
        alertas = []

        lucro_12m = dados.get("lucro_liquido_12m") or 0
        receita_12m = dados.get("receita_12m") or 1
        ebit_12m = dados.get("ebit_12m") or 0
        patrimonio = dados.get("patrimonio_liq") or 1
        divida_liq = dados.get("divida_liquida") or 0
        roe = dados.get("roe") or 0
        margem_liq = dados.get("margem_liquida") or 0
        liq_corrente = dados.get("liquidez_corrente") or 0

        # Estimar EBITDA a partir de EBIT + margem (aproximacao)
        ebitda_12m = ebit_12m * 1.15 if ebit_12m else 0

        # 1.1 Prejuizo liquido
        if lucro_12m < 0:
            sev = "CRITICO" if margem_liq < self.MARGEM_LIQUIDA_CRITICA else "ALTO"
            alertas.append(Alerta(
                ticker=ticker,
                tipo="PREJUIZO_LIQUIDO",
                severidade=sev,
                titulo=f"Prejuizo de R$ {abs(lucro_12m) / 1e6:.0f}M nos ultimos 12 meses",
                descricao=(
                    f"Margem liquida: {margem_liq:.1f}%. "
                    "Empresa esta consumindo patrimonio."
                ),
                valor_detectado=lucro_12m,
            ))

        # 1.2 Endividamento excessivo
        if ebitda_12m and ebitda_12m > 0 and divida_liq > 0:
            dliq_ebitda = divida_liq / ebitda_12m
            if dliq_ebitda > self.DIVIDA_EBITDA_CRITICO:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="ENDIVIDAMENTO_CRITICO",
                    severidade="CRITICO",
                    titulo=f"Div.Liq/EBITDA: {dliq_ebitda:.1f}x (critico > {self.DIVIDA_EBITDA_CRITICO}x)",
                    descricao="Endividamento muito elevado. Risco de insolvencia.",
                    valor_detectado=dliq_ebitda,
                    threshold_usado=self.DIVIDA_EBITDA_CRITICO,
                ))
            elif dliq_ebitda > self.DIVIDA_EBITDA_ALTO:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="ENDIVIDAMENTO_ALTO",
                    severidade="ALTO",
                    titulo=f"Div.Liq/EBITDA: {dliq_ebitda:.1f}x (alto > {self.DIVIDA_EBITDA_ALTO}x)",
                    descricao="Endividamento elevado. Monitorar capacidade de refinanciamento.",
                    valor_detectado=dliq_ebitda,
                    threshold_usado=self.DIVIDA_EBITDA_ALTO,
                ))

        # 1.3 ROE negativo
        if roe < 0:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="ROE_NEGATIVO",
                severidade="ALTO",
                titulo=f"ROE negativo: {roe:.1f}%",
                descricao="Empresa nao gera retorno sobre o patrimonio dos acionistas.",
                valor_detectado=roe,
            ))

        # 1.4 Liquidez corrente baixa
        if liq_corrente and 0 < liq_corrente < 0.8:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="LIQUIDEZ_BAIXA",
                severidade="MEDIO",
                titulo=f"Liquidez corrente: {liq_corrente:.2f} (abaixo de 0.80)",
                descricao="Ativo circulante insuficiente para cobrir passivo circulante de curto prazo.",
                valor_detectado=liq_corrente,
                threshold_usado=0.8,
            ))

        return alertas

    # ================================================================
    # CRUZAMENTO 2: Divergencia Lucro vs Caixa
    # ================================================================
    def analisar_divergencia_lucro_resultados(
        self, ticker: str, dados: dict
    ) -> List[Alerta]:
        """
        Compara lucro dos ultimos 12m vs ultimos 3m anualizado.
        Divergencia grande pode indicar deterioracao ou melhora recente.
        """
        alertas = []

        lucro_12m = dados.get("lucro_liquido_12m") or 0
        lucro_3m = dados.get("lucro_liquido_3m") or 0
        receita_12m = dados.get("receita_12m") or 0
        receita_3m = dados.get("receita_3m") or 0

        if not lucro_12m or not lucro_3m:
            return alertas

        # Anualizar o trimestre
        lucro_3m_anualizado = lucro_3m * 4

        # Divergencia: trimestre muito pior que media anual
        if lucro_12m > 0 and lucro_3m < 0:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="TRIMESTRE_PREJUIZO",
                severidade="MEDIO",
                titulo=f"Ultimo trimestre com prejuizo de R$ {abs(lucro_3m) / 1e6:.0f}M apesar de lucro anual",
                descricao=(
                    f"Lucro 12m: R$ {lucro_12m / 1e6:.0f}M, mas ultimo trimestre negativo. "
                    "Possivel deterioracao recente dos resultados."
                ),
                valor_detectado=lucro_3m,
            ))

        # Receita trimestral caindo vs media anual
        if receita_12m > 0 and receita_3m > 0:
            receita_media_trim = receita_12m / 4
            variacao = (receita_3m / receita_media_trim - 1) * 100
            if variacao < -15:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="RECEITA_CAINDO",
                    severidade="MEDIO",
                    titulo=f"Receita trimestral {variacao:.0f}% abaixo da media anual",
                    descricao=(
                        f"Receita trim: R$ {receita_3m / 1e6:.0f}M vs media anual de "
                        f"R$ {receita_media_trim / 1e6:.0f}M/trim. Queda significativa."
                    ),
                    valor_detectado=variacao,
                    threshold_usado=-15.0,
                ))

        # Trimestre muito melhor que media (possivel evento nao recorrente)
        if lucro_12m > 0 and lucro_3m > 0:
            lucro_medio_trim = lucro_12m / 4
            if lucro_medio_trim > 0:
                ratio = lucro_3m / lucro_medio_trim
                if ratio > 2.5:
                    alertas.append(Alerta(
                        ticker=ticker,
                        tipo="LUCRO_EXTRAORDINARIO",
                        severidade="INFO",
                        titulo=f"Lucro trimestral {ratio:.1f}x acima da media - possivel evento nao recorrente",
                        descricao=(
                            f"Lucro trim: R$ {lucro_3m / 1e6:.0f}M vs media de "
                            f"R$ {lucro_medio_trim / 1e6:.0f}M/trim. Verificar se e sustentavel."
                        ),
                        valor_detectado=ratio,
                    ))

        return alertas

    # ================================================================
    # CRUZAMENTO 3: Valuation vs Pares do Setor
    # ================================================================
    def analisar_valuation_vs_setor(
        self,
        ticker: str,
        indicadores: dict,
        mediana_setor: dict,
        nome_setor: str,
    ) -> List[Alerta]:
        """Compara indicadores da empresa com mediana do seu setor."""
        alertas = []

        comparacoes = [
            ("pl", "P/L", True, 2.0),
            ("pvp", "P/VP", True, 2.0),
            ("ev_ebitda", "EV/EBITDA", True, 2.0),
            ("roe", "ROE", False, 1.5),
        ]

        for campo, nome, alto_e_caro, fator in comparacoes:
            val = indicadores.get(campo)
            med = mediana_setor.get(campo)
            if not val or not med or med == 0:
                continue

            # Para P/L, P/VP: ignorar valores negativos
            if alto_e_caro and (val <= 0 or med <= 0):
                continue

            ratio = val / med

            if alto_e_caro:
                if ratio > fator:
                    alertas.append(Alerta(
                        ticker=ticker,
                        tipo="VALUATION_CARO",
                        severidade="MEDIO",
                        titulo=f"{nome}: {val:.1f}x ({ratio:.1f}x a mediana do setor: {med:.1f}x)",
                        descricao=f"Empresa negociada a premio vs setor {nome_setor}.",
                        valor_detectado=val,
                        threshold_usado=med,
                    ))
                elif ratio < (1 / fator):
                    alertas.append(Alerta(
                        ticker=ticker,
                        tipo="VALUATION_BARATO",
                        severidade="INFO",
                        titulo=f"{nome}: {val:.1f}x abaixo da mediana ({med:.1f}x) no setor {nome_setor}",
                        descricao="Possivel subvalorizacao. Verificar se ha motivo fundamental.",
                        valor_detectado=val,
                        threshold_usado=med,
                    ))
            else:
                # Para ROE: menor que metade do setor e ruim
                if ratio < 0.5:
                    alertas.append(Alerta(
                        ticker=ticker,
                        tipo="RENTABILIDADE_BAIXA_VS_SETOR",
                        severidade="MEDIO",
                        titulo=f"{nome}: {val:.1f}% (menos da metade da mediana: {med:.1f}%)",
                        descricao=f"Rentabilidade muito abaixo dos pares no setor {nome_setor}.",
                        valor_detectado=val,
                        threshold_usado=med,
                    ))

        return alertas

    # ================================================================
    # CRUZAMENTO 4: Impacto Macro nos Setores
    # ================================================================
    def analisar_impacto_macro(
        self,
        ticker: str,
        setor: str,
        macro: dict,
    ) -> List[Alerta]:
        """
        macro: {selic_atual, selic_6m_atras, cambio_atual, cambio_6m_atras}
        """
        alertas = []
        if not setor or not macro:
            return alertas

        selic = macro.get("selic_atual", 0)
        selic_ant = macro.get("selic_6m_atras", selic)
        cambio = macro.get("cambio_atual", 0)
        cambio_ant = macro.get("cambio_6m_atras", cambio)

        selic_alto = selic > 12.0
        cambio_subindo = cambio > cambio_ant * 1.05 if cambio_ant else False

        setor_upper = setor.upper()

        SELIC_NEGATIVO = ["VAREJO", "CONSTRUCAO", "CONSUMO", "LOCACAO", "SHOPPING", "IMOBILIARIO"]
        SELIC_POSITIVO = ["BANCO", "SEGURO", "FINANCEIRO"]
        DOLAR_POSITIVO = ["MINERACAO", "SIDERURGIA", "PAPEL", "CELULOSE", "PETROLEO", "AGRO"]
        DOLAR_NEGATIVO = ["AVIACAO", "TRANSPORTE"]

        if selic_alto and any(s in setor_upper for s in SELIC_NEGATIVO):
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_SELIC_PRESSAO",
                severidade="MEDIO",
                titulo=f"SELIC em {selic:.1f}% pressiona setor {setor}",
                descricao="Juros altos encarecem credito e reduzem consumo neste setor.",
                valor_detectado=selic,
            ))

        if selic_alto and any(s in setor_upper for s in SELIC_POSITIVO):
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_SELIC_BENEFICIO",
                severidade="INFO",
                titulo=f"SELIC em {selic:.1f}% beneficia setor {setor}",
                descricao="Setor tende a se beneficiar de juros elevados (spread bancario maior).",
                valor_detectado=selic,
            ))

        if cambio_subindo and any(s in setor_upper for s in DOLAR_POSITIVO):
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_CAMBIO_BENEFICIO",
                severidade="INFO",
                titulo=f"Dolar em alta beneficia setor {setor}",
                descricao="Receitas atreladas ao dolar crescem com valorizacao cambial.",
                valor_detectado=cambio,
            ))

        if cambio_subindo and any(s in setor_upper for s in DOLAR_NEGATIVO):
            alertas.append(Alerta(
                ticker=ticker,
                tipo="MACRO_CAMBIO_PRESSAO",
                severidade="MEDIO",
                titulo=f"Dolar em alta pressiona setor {setor}",
                descricao="Custos atrelados ao dolar aumentam com valorizacao cambial.",
                valor_detectado=cambio,
            ))

        return alertas

    # ================================================================
    # CRUZAMENTO 5: Consistencia de Dividendos
    # ================================================================
    def analisar_dividendos(
        self,
        ticker: str,
        dados: dict,
        selic_atual: float,
        anos_consecutivos: int = 0,
    ) -> List[Alerta]:
        """Avalia sustentabilidade e atratividade dos dividendos."""
        alertas = []

        dy = dados.get("dividend_yield") or 0
        lucro_12m = dados.get("lucro_liquido_12m") or 0
        cotacao = dados.get("cotacao") or 0
        num_acoes = dados.get("num_acoes") or 0

        if dy <= 0 or cotacao <= 0:
            return alertas

        # Estimar payout: dividendo por acao / LPA
        lpa = dados.get("lpa") or 0
        if lpa and lpa > 0:
            dividendo_por_acao = cotacao * (dy / 100)
            payout = (dividendo_por_acao / lpa) * 100

            if payout > 100:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="DIVIDENDO_INSUSTENTAVEL",
                    severidade="ALTO",
                    titulo=f"Payout estimado: {payout:.0f}% - distribui mais do que lucra",
                    descricao=(
                        f"DY: {dy:.1f}%, LPA: R$ {lpa:.2f}. "
                        "Dividendo provavelmente sera reduzido nos proximos periodos."
                    ),
                    valor_detectado=payout,
                    threshold_usado=100.0,
                ))
            elif payout > 85:
                alertas.append(Alerta(
                    ticker=ticker,
                    tipo="PAYOUT_ALTO",
                    severidade="MEDIO",
                    titulo=f"Payout estimado: {payout:.0f}% - pouca margem de seguranca",
                    descricao="Empresa distribui quase todo o lucro. Pouca retencao para crescimento.",
                    valor_detectado=payout,
                    threshold_usado=85.0,
                ))

        # DY abaixo da SELIC (renda fixa mais atrativa)
        if selic_atual > 0 and dy < selic_atual * 0.7:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="DY_ABAIXO_SELIC",
                severidade="INFO",
                titulo=f"DY ({dy:.1f}%) muito abaixo da SELIC ({selic_atual:.1f}%)",
                descricao="Renda fixa oferece retorno superior ao dividend yield desta acao.",
                valor_detectado=dy,
                threshold_usado=selic_atual,
            ))

        # DY alto - pode ser armadilha ou oportunidade
        if dy > 12:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="DY_MUITO_ALTO",
                severidade="MEDIO",
                titulo=f"DY muito alto: {dy:.1f}% - verificar sustentabilidade",
                descricao=(
                    "DY acima de 12% pode indicar: (1) queda recente no preco da acao, "
                    "(2) dividendo extraordinario nao recorrente, ou (3) oportunidade genuina."
                ),
                valor_detectado=dy,
            ))

        # Consistencia (se informada)
        if anos_consecutivos >= 5:
            alertas.append(Alerta(
                ticker=ticker,
                tipo="DIVIDENDO_CONSISTENTE",
                severidade="INFO",
                titulo=f"Pagamento de dividendos por {anos_consecutivos} anos consecutivos",
                descricao="Historico solido de distribuicao de proventos.",
                valor_detectado=float(anos_consecutivos),
            ))

        return alertas
