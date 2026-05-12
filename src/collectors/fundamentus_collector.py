import fundamentus
import pandas as pd
from loguru import logger


class FundamentusCollector:
    """Coleta dados fundamentalistas do site fundamentus.com.br via scraping."""

    def get_papel(self, ticker: str) -> dict:
        """
        Retorna dados detalhados de um ticker.
        Campos disponiveis: Cotacao, PL, PVP, ROE, ROIC, Div_Yield,
        Marg_Bruta, Marg_Liquida, Div_Br_Patrim, EBIT, Lucro_Liquido, etc.
        """
        try:
            df = fundamentus.get_papel(ticker)
            if df is None or df.empty:
                raise ValueError(f"Ticker {ticker} nao encontrado no Fundamentus.")
            row = df.iloc[0].to_dict()
            return self._normalizar(row)
        except Exception as e:
            logger.error(f"Erro Fundamentus [{ticker}]: {e}")
            raise

    def get_todos(self) -> pd.DataFrame:
        """
        Retorna screening de todas as acoes com indicadores basicos.
        Colunas: Cotacao, PL, PVP, PSR, DY, Patrim_Liq, Div_Bruta, etc.
        """
        try:
            df = fundamentus.get_resultado()
            logger.info(f"Fundamentus: {len(df)} acoes retornadas no screening.")
            return df
        except Exception as e:
            logger.error(f"Erro Fundamentus screening: {e}")
            return pd.DataFrame()

    def _normalizar(self, row: dict) -> dict:
        """Converte campos do Fundamentus para formato padrao do sistema."""

        def parse_pct(val):
            if isinstance(val, str):
                val = val.replace("%", "").replace(",", ".").strip()
                if not val or val == "-":
                    return 0
                return float(val)
            return float(val) if val else 0

        def parse_num(val):
            if val is None:
                return None
            if isinstance(val, str):
                val = val.replace(".", "").replace(",", ".").strip()
                if not val or val == "-":
                    return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # Fundamentus retorna valores multiplicados por 100 (ex: PL=564 -> 5.64)
        def div100(val):
            v = parse_num(val)
            return round(v / 100, 2) if v is not None else None

        return {
            "ticker":           row.get("Papel"),
            "empresa":          row.get("Empresa"),
            "setor":            row.get("Setor"),
            "subsetor":         row.get("Subsetor"),
            "cotacao":          div100(row.get("Cotacao")),
            "data_cotacao":     row.get("Data_ult_cot"),
            "min_52sem":        div100(row.get("Min_52_sem")),
            "max_52sem":        div100(row.get("Max_52_sem")),
            "market_cap":       parse_num(row.get("Valor_de_mercado")),
            "enterprise_value": parse_num(row.get("Valor_da_firma")),
            "num_acoes":        parse_num(row.get("Nro_Acoes")),
            # Valuation (divididos por 100)
            "pl":               div100(row.get("PL")),
            "pvp":              div100(row.get("PVP")),
            "psr":              div100(row.get("PSR")),
            "p_ebit":           div100(row.get("PEBIT")),
            "p_ativos":         div100(row.get("PAtivos")),
            "ev_ebitda":        div100(row.get("EV_EBITDA")),
            "ev_ebit":          div100(row.get("EV_EBIT")),
            "dividend_yield":   parse_pct(row.get("Div_Yield")),
            # Rentabilidade (ja vem em %)
            "roe":              parse_pct(row.get("ROE")),
            "roic":             parse_pct(row.get("ROIC")),
            "margem_bruta":     parse_pct(row.get("Marg_Bruta")),
            "margem_ebit":      parse_pct(row.get("Marg_EBIT")),
            "margem_liquida":   parse_pct(row.get("Marg_Liquida")),
            # Endividamento
            "divida_bruta":     parse_num(row.get("Div_Bruta")),
            "divida_liquida":   parse_num(row.get("Div_Liquida")),
            "patrimonio_liq":   parse_num(row.get("Patrim_Liq")),
            "div_bruta_pl":     div100(row.get("Div_Br_Patrim")),
            "liquidez_corrente":div100(row.get("Liquidez_Corr")),
            # Resultados
            "ativo_total":      parse_num(row.get("Ativo")),
            "disponibilidades": parse_num(row.get("Disponibilidades")),
            "receita_12m":      parse_num(row.get("Receita_Liquida_12m")),
            "ebit_12m":         parse_num(row.get("EBIT_12m")),
            "lucro_liquido_12m":parse_num(row.get("Lucro_Liquido_12m")),
            "receita_3m":       parse_num(row.get("Receita_Liquida_3m")),
            "ebit_3m":          parse_num(row.get("EBIT_3m")),
            "lucro_liquido_3m": parse_num(row.get("Lucro_Liquido_3m")),
            # Crescimento
            "cres_rec_5a":      parse_pct(row.get("Cres_Rec_5a")),
            # Por acao (divididos por 100)
            "lpa":              div100(row.get("LPA")),
            "vpa":              div100(row.get("VPA")),
        }
