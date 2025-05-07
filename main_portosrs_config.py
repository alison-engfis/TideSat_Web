'''
Arquivo que contém todas as informações consideradas constantes
para o funcionamento do fluxo da lógica do atual script main-alt.py.

'''

################# FUSO PADRÃO #################
TIMEZONE_PADRAO = "America/Sao_Paulo"


################# CONFIGURAÇÕES DO SITE PRINCIPAL #################
ESTACOES_PORTOS = {
    "EST1": {
        "descricao": "EST1 - Rio Taquari (Foz do Boa Vista)",
        "url": "https://app.tidesatglobal.com/est1/est1_out.csv",
        "coord": [-29.471768, -51.956703],
        "descricao_imagem": "Estação EST1 - Porto de Estrela",
        "caminho_imagem": " ",
        "cota_alerta": 17.00,
        "cota_inundacao": 19.00
    },

    "ITA1": {
        "descricao": "ITA1 - Guaíba (Farol de Itapuã)",
        "url": "https://app.tidesatglobal.com/ita1/ita1_out.csv",
        "coord": [-30.385119, -51.059579],
        "descricao_imagem": "Estação ITA1 - Guaíba (Farol de Itapuã)",
        "caminho_imagem": "ita1_photo.jpg",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    
    "NVG1": {
        "descricao": "NVG1 - Bairro Navegantes",
        "url": "https://app.tidesatglobal.com/nvg1/nvg1_out.csv",
        "coord": [-30.096215, -51.260051], 
        "descricao_imagem": " ",
        "caminho_imagem": " ",
        "cota_alerta": 1.80,
        "cota_inundacao": 2.50
    },

    "SPH4": {
        "descricao": "SPH4 - Guaíba (Av. Mauá)",
        "url": "https://app.tidesatglobal.com/sph4/sph4_out.csv",
        "coord": [-30.02703, -51.23166],
        "descricao_imagem": "Estação SPH4 - Guaíba (Av. Mauá)",
        "caminho_imagem": "sph4_photo.jpg",
        "cota_alerta": 2.50,
        "cota_inundacao": 3.00
    },
    "STH1": {
        "descricao": "STH1 - Fábrica Stihl (São Leopoldo)",
        "url": "https://app.tidesatglobal.com/sth1/sth1_out.csv",
        "coord": [-29.787741, -51.109447],
        "descricao_imagem": "Estação STH1 - Fábrica Stihl (São Leopoldo)",
        "caminho_imagem": "STH1_photo.jpg",
        "cota_alerta": " ",
        "cota_inundacao": " "
    }
}

ESTACAO_PADRAO_PORTOS = "EST1"