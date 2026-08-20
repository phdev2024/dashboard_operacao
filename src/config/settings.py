"""
Módulo de Configurações Globais da Aplicação (Settings)
"""

from pathlib import Path

# --- DIRETÓRIOS BASE DO PROJETO ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Pastas Oficiais de Saída
PASTA_STATUS_SAIDA = DATA_DIR / "status_saida"
PASTA_OPERACIONAL_SAIDA = PASTA_STATUS_SAIDA / "operacional"
PASTA_HISTORICO_SAIDA = PASTA_STATUS_SAIDA / "historico"

# Outras operações
PASTA_ENTRADA = DATA_DIR / "entrada"
PASTA_TRANSPORTE = DATA_DIR / "transporte"

# Identidade Visual e Layout
BRAND_NAME = "LOGCARE LOGÍSTICA"
APP_TITLE = "Painel Operacional - Pedidos Diários"

COLOR_BRAND_PRIMARY = "#00BBA9"
COLOR_BRAND_SECONDARY = "#069782"
COLOR_BRAND_DARK = "#2D655A"

COLOR_BG_DARK = "#0B1311"
COLOR_CARD_BG = "#162421"
COLOR_CARD_BORDER = "#223834"

COLOR_SUCCESS = "#00E676"
COLOR_WARNING = "#FFD600"
COLOR_DANGER = "#FF1744"

COLOR_TEXT_LIGHT = "#FFFFFF"
COLOR_TEXT_MUTED = "#8DAA9D"

PAGE_CONFIG = {
    "page_title": "Logcare - Painel Operacional",
    "page_icon": "🦅",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

DEFAULT_OPERATIONAL_YEAR = 2026