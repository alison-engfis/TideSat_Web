'''
Arquivo que dá início a execução do domínio tidesat-barroso.streamlit.app
e a todo o fluxo de importações dos outros arquivos em main_gen.py,
levando as informações constantes pertinentes a esse script.

'''

# SITE ESCOLA ALMIRANTE BARROSO
import streamlit as st
from tools import main, checar_senha
from main_barroso_config import ESTACOES_BARROSO, ESTACAO_PADRAO_BARROSO

if not checar_senha():
    st.stop()
estacoes_info = ESTACOES_BARROSO
estacao_padrao = ESTACAO_PADRAO_BARROSO
logotipo = "TideSat_logo.webp"
html_logo = "https://www.tidesatglobal.com/"

main(estacoes_info, estacao_padrao, logotipo, html_logo)