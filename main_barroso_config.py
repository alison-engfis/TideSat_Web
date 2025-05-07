'''
Arquivo que contém todas as informações consideradas constantes
para o funcionamento do fluxo da lógica do atual script main-alt.py.

'''

################# FUSO PADRÃO #################
TIMEZONE_PADRAO = "America/Sao_Paulo"


################# CONFIGURAÇÕES DO SITE ALMIRANTE BARROSO #################
ESTACOES_BARROSO = {
    "IDP1": {
        "descricao": "IDP1 - Guaíba (Estaleiro Mabilde)",
        "url": "https://app.tidesatglobal.com/idp1/idp1_out.csv",
        "coord": [-30.029811, -51.25147],
        "descricao_imagem": "Estação IDP1 - Guaíba (Arquipélago)",
        "caminho_imagem": "idp1_photo.jpg",
        "cota_alerta": 1.85, 
        "cota_inundacao": 2.05
    }
}

ESTACAO_PADRAO_BARROSO = "IDP1"