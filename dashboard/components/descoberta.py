"""
Pools e funções para 'Descobertas do Dia' e 'Joias Escondidas'.

A aleatoriedade aqui é **determinística por dia** (mesma seed -> mesmo resultado),
para garantir reprodutibilidade. O usuário pode forçar uma nova amostra ajustando
um offset de seed.
"""
import hashlib
import random
from datetime import date


# Universo ampliado de ações líquidas da B3 (~85 tickers cobrindo todos os setores)
POOL_AMPLO = [
    # Petróleo e Gás
    "PETR3", "PETR4", "PRIO3", "RECV3", "RRRP3", "CSAN3", "UGPA3", "VBBR3",
    # Mineração e Siderurgia
    "VALE3", "CSNA3", "GGBR4", "USIM5", "GOAU4", "BRAP4",
    # Bancos e Financeiro
    "ITUB4", "ITUB3", "BBAS3", "BBDC4", "BBDC3", "SANB11", "BPAC11", "ITSA4",
    "B3SA3", "ABCB4", "BRSR6", "BMGB4", "BIDI11", "PINE4",
    # Seguros
    "BBSE3", "PSSA3", "IRBR3", "CXSE3",
    # Energia Elétrica
    "EGIE3", "ENGI11", "CPFE3", "TAEE11", "CMIG4", "CMIG3", "EQTL3", "ENEV3",
    "ELET3", "ELET6", "CPLE6", "NEOE3", "AURE3", "CEBR6",
    # Saneamento e Utilidades
    "SBSP3", "SAPR11", "CSMG3", "SAPR4", "CASN3",
    # Varejo e Consumo
    "MGLU3", "LREN3", "PETZ3", "ARZZ3", "AMER3", "VVAR3", "ASAI3", "SOMA3",
    "GUAR3", "VIIA3", "ALPA4", "CEAB3", "MULT3", "IGTI11",
    # Agronegócio e Alimentos
    "SLCE3", "BEEF3", "SMTO3", "AGRO3", "JBSS3", "BRFS3", "MRFG3", "TTEN3",
    "CSUD3", "MDIA3", "RAIZ4",
    # Bebidas e Alimentos processados
    "ABEV3", "NTCO3", "CAML3", "JALL3",
    # Saúde
    "RDOR3", "HAPV3", "FLRY3", "HYPE3", "QUAL3", "DASA3", "RADL3", "PNVL3",
    "ONCO3", "BLAU3", "VIVA3",
    # Telecomunicações
    "VIVT3", "TIMS3", "OIBR3",
    # Papel e Celulose
    "SUZB3", "KLBN11", "KLBN4", "IRANI3",
    # Tecnologia
    "TOTS3", "LWSA3", "POSI3", "INTB3", "CASH3", "MELI34",
    # Construção Civil e Imobiliário
    "CYRE3", "MRVE3", "EZTC3", "TEND3", "GFSA3", "DIRR3", "PLPL3", "MOAR3",
    "EVEN3", "TRIS3", "JHSF3", "LAVV3",
    # Transporte, Logística e Aviação
    "CCRO3", "RENT3", "AZUL4", "EMBR3", "MOVI3", "VAMO3", "STBP3", "LOGN3",
    "RAIL3", "GOLL4",
    # Indústria e Bens de Capital
    "WEGE3", "ROMI3", "FRAS3", "POMO4", "TUPY3", "KEPL3", "MILS3", "RANI3",
    # Educação
    "COGN3", "YDUQ3", "CSED3", "ANIM3", "SEER3",
    # Outros
    "SBSP3", "JBSS3", "BRKM5", "UNIP6", "FESA4", "DXCO3",
]

# Remove duplicatas mantendo ordem
POOL_AMPLO = list(dict.fromkeys(POOL_AMPLO))


# Blue chips mais óbvias (excluídas no modo "Joias Escondidas")
BLUE_CHIPS = {
    "PETR3", "PETR4", "VALE3", "ITUB4", "ITUB3", "BBDC4", "BBDC3",
    "BBAS3", "ABEV3", "MGLU3", "WEGE3", "B3SA3", "ELET3", "ELET6",
    "RENT3", "RDOR3", "JBSS3", "SUZB3", "LREN3", "VIVT3", "ITSA4",
}


def _seed_do_dia(offset: int = 0, salt: str = "descobertas") -> int:
    """
    Gera seed determinística a partir da data + offset opcional.
    Mesmo dia + offset = mesmo resultado. Mudando offset, muda o sorteio.
    """
    chave = f"{salt}-{date.today().isoformat()}-{offset}"
    h = hashlib.sha256(chave.encode()).hexdigest()
    return int(h[:8], 16)


def descobertas_do_dia(quantidade: int = 25, offset: int = 0) -> list[str]:
    """
    Sorteia N tickers do pool ampliado usando seed do dia.
    Mesmo dia + offset = mesma lista. Tudo reproduzível.
    """
    rng = random.Random(_seed_do_dia(offset, salt="descobertas"))
    n = min(quantidade, len(POOL_AMPLO))
    return rng.sample(POOL_AMPLO, n)


def joias_escondidas(quantidade: int = 25, offset: int = 0) -> list[str]:
    """
    Sorteia tickers do pool ampliado EXCLUINDO as blue chips mais óbvias.
    Foco em mid/small caps que o usuário provavelmente não acompanha.
    """
    pool_filtrado = [t for t in POOL_AMPLO if t not in BLUE_CHIPS]
    rng = random.Random(_seed_do_dia(offset, salt="joias"))
    n = min(quantidade, len(pool_filtrado))
    return rng.sample(pool_filtrado, n)
