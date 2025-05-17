'''
Arquivo que dá início a execução do domínio tidesat-ipatinga.streamlit.app
e a todo o fluxo de importações dos outros arquivos em main_gen.py,
levando as informações constantes pertinentes a esse script.

'''

# SITE DE IPATINGA
from main_ipatinga_config import ESTACOES_IPATINGA, ESTACAO_PADRAO_IPATINGA
from tools import main
from language import LANG

# Define o idioma para essa instância
idioma = "pt"
lang = LANG[idioma]

estacoes_info = ESTACOES_IPATINGA
estacao_padrao = ESTACAO_PADRAO_IPATINGA
logotipo = "TideSat_logo.webp"
html_logo = "https://www.tidesatglobal.com/"

main(estacoes_info, estacao_padrao, logotipo, html_logo, lang)