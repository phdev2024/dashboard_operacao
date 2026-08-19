"""
Módulo de Configurações Globais da Aplicação (Settings)
Centraliza a paleta de cores da LOGCARE, regras de layout e visualização da TV.
"""

"""
Módulo de Configurações Globais da Aplicação (Settings)
"""

from pathlib import Path

# --- DIRETÓRIOS BASE DO PROJETO ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

# Pastas de dados operacionais
PASTA_STATUS_SAIDA = DATA_DIR / "saida"
PASTA_ENTRADA = DATA_DIR / "entrada"
PASTA_TRANSPORTE = DATA_DIR / "transporte"


# Identidade do Produto
BRAND_NAME = "LOGCARE LOGÍSTICA"
APP_TITLE = "Painel Operacional - Pedidos Diários"

# Paleta Oficial LOGCARE & Ajustes de Alto Contraste para TV
COLOR_BRAND_PRIMARY = "#00BBA9"    # Verde menta vibrante do logo (Destaque Principal)
COLOR_BRAND_SECONDARY = "#069782"  # Verde turquesa intermediário
COLOR_BRAND_DARK = "#2D655A"       # Verde escuro institucional

# Estrutura Dark Mode para Leitura de Longe
COLOR_BG_DARK = "#0B1311"          # Fundo escuro levemente esverdeado
COLOR_CARD_BG = "#162421"          # Fundo dos cards operacionais
COLOR_CARD_BORDER = "#223834"      # Borda sutil dos cards

# Indicadores de Status Operacional
COLOR_SUCCESS = "#00E676"          # Verde Neon (Concluído/OK)
COLOR_WARNING = "#FFD600"          # Amarelo (Em Separação/Atenção)
COLOR_DANGER = "#FF1744"           # Vermelho Alerta (Atrasado/Pendente)

# Tipografia
COLOR_TEXT_LIGHT = "#FFFFFF"       # Texto principal
COLOR_TEXT_MUTED = "#8DAA9D"       # Texto secundário / rótulos

# Configurações do Streamlit
PAGE_CONFIG = {
    "page_title": "Logcare - Painel Operacional",
    "page_icon": "🦅",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# Filtro Padrão da Operação
DEFAULT_OPERATIONAL_YEAR = 2026