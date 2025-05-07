'''
Arquivo que contém todas as informações consideradas constantes
para o funcionamento do fluxo da lógica do atual script main-ipatinga.py.

'''

################# FUSO PADRÃO #################
TIMEZONE_PADRAO = "America/Sao_Paulo"


################# CONFIGURAÇÕES PARA IPATINGA #################
ESTACOES_IPATINGA = {
    "IPA2": {
        "descricao": "IPA2 - Ipatinga (MG)",
        "url": "https://app.tidesatglobal.com/ipa2/ipa2_out.csv",
        "coord": "",
        "descricao_imagem": "Estação IPA2 - Ipatinga (MG)",
        "caminho_imagem": "",
        "cota_alerta": " ", 
        "cota_inundacao": " "
    }
}

ESTACAO_PADRAO_IPATINGA = "IPA2"
