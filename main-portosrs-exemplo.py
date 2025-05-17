from main_portosrs_config import ESTACOES_PORTOS, ESTACAO_PADRAO_PORTOS
from tools import main
from language import LANG

# Define o idioma para essa instância
idioma = "en"
lang = LANG[idioma]

# Informações específicas da dashboard
estacoes_info = ESTACOES_PORTOS
estacao_padrao = ESTACAO_PADRAO_PORTOS
logotipo = "portosrs_logo.png"
html_logo = "https://www.portosrs.com.br/site/"

# Executa o app com a linguagem definida
main(estacoes_info, estacao_padrao, logotipo, html_logo, lang)