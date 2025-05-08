'''
Arquivo que dá início a execução do domínio tidesat-estrela.streamlit.app
e a todo o fluxo de importações dos outros arquivos em main_gen.py,
levando as informações constantes pertinentes a esse script.

'''

# SITE DE ESTRELA
from main_estrela_alt import ESTACOES_ESTRELA, ESTACAO_PADRAO_ESTRELA
from tools import main

estacoes_info = ESTACOES_ESTRELA
estacao_padrao = ESTACAO_PADRAO_ESTRELA
logotipo = "TideSat_logo.webp"
html_logo = "https://www.tidesatglobal.com/"

main(estacoes_info, estacao_padrao, logotipo, html_logo)
