'''
Arquivo que dá início a execução do domínio tidesat.streamlit.app
e a todo o fluxo de importações dos outros arquivos em main_gen.py,
levando as informações constantes pertinentes a esse script.

'''

# SITE PRINCIPAL
from main_config import ESTACOES, ESTACAO_PADRAO
from tools import main
from language import LANG

# Define o idioma para essa instância
idioma = "pt"
lang = LANG[idioma]

estacoes_info = ESTACOES
estacao_padrao = ESTACAO_PADRAO

main(estacoes_info, estacao_padrao, lang)