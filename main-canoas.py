'''
Arquivo que dá início a execução do domínio tidesat-canoas.streamlit.app
e a todo o fluxo de importações dos outros arquivos em main_canoas_config.py,
levando as informações constantes pertinentes a esse script.

'''

# SITE DE CANOAS
from main_canoas_config import ESTACOES_CANOAS, ESTACAO_PADRAO_CANOAS
from tools import main

estacoes_info = ESTACOES_CANOAS
estacao_padrao = ESTACAO_PADRAO_CANOAS
logotipo = "metsul_logo.png"
html_logo = "https://metsul.com/"

main(estacoes_info, estacao_padrao, logotipo, html_logo)