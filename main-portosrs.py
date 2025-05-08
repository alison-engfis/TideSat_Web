'''
Arquivo que dá início a execução do domínio tidesat-portosrs.streamlit.app
e a todo o fluxo de importações dos outros arquivos em main_gen.py,
levando as informações constantes pertinentes a esse script.

'''

# SITE PARA PORTOSRS
from main_portosrs_config import ESTACOES_PORTOS, ESTACAO_PADRAO_PORTOS
from tools import main

estacoes_info = ESTACOES_PORTOS
estacao_padrao = ESTACAO_PADRAO_PORTOS
logotipo = "portosrs_logo.png"
html_logo = "https://www.portosrs.com.br/site/"

main(estacoes_info, estacao_padrao, logotipo, html_logo)