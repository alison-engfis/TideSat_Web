'''
Arquivo que contém todas as informações consideradas constantes
para o funcionamento do fluxo da lógica do atual script main-alt.py.

'''

################# FUSO PADRÃO #################
TIMEZONE_PADRAO = "America/Sao_Paulo"


################# CONFIGURAÇÕES DO SITE PRINCIPAL #################
ESTACOES = {
    "ACT1": {
        "descricao": "ACT1 - Arroio Cavalhada",
        "url": "https://app.tidesatglobal.com/act1/act1_out.csv",
        "coord": [-30.09157, -51.248928],
        "descricao_imagem": "Estação ACT1 - Arroio Cavalhada",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "

    },
    "ADV3": {
        "descricao": "ADV3 - Arroio Dilúvio",
        "url": "https://app.tidesatglobal.com/adv3/adv3_out.csv",
        "coord": [-30.047258, -51.197514],
        "descricao_imagem": "Estação ADV3 - Arroio Dilúvio",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    "EST1": {
        "descricao": "EST1 - Rio Taquari (Foz do Boa Vista)",
        "url": "https://app.tidesatglobal.com/est1/est1_out.csv",
        "coord": [-29.471768, -51.956703],
        "descricao_imagem": "Estação EST1 - Porto de Estrela",
        "caminho_imagem": " ",
        "cota_alerta": 17.00,
        "cota_inundacao": 19.00
    },
    "IDP1": {
        "descricao": "IDP1 - Guaíba (Arquipélago)",
        "url": "https://app.tidesatglobal.com/idp1/idp1_out.csv",
        "coord": [-30.029811, -51.25147],
        "descricao_imagem": "Estação IDP1 - Guaíba (Arquipélago)",
        "caminho_imagem": "idp1_photo.jpg",
        "cota_alerta": 1.85, 
        "cota_inundacao": 2.05
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
    "RIG1": {
        "descricao": "RIG1 - Centro de Rio Grande",
        "url": "https://app.tidesatglobal.com/rig1/rig1_out.csv",
        "coord": [-32.026822, -52.103654],
        "descricao_imagem": "Estação RIG1 - Centro de Rio Grande",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    "RLS1": {
        "descricao": "RLS1 - Represa (Lomba do Sabão)",
        "url": "https://app.tidesatglobal.com/rls1/rls1_out.csv",
        "coord": [-30.0840741, -51.1110800],
        "descricao_imagem": "Estação RLS1 - Represa (Lomba do Sabão)",
        "caminho_imagem": "rls1_photo.jpg",
        "cota_alerta": " ",
        "cota_inundacao": " "
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
    },
    "VDS1": {
        "descricao": "VDS1 - Guaíba (Vila Assunção)",
        "url": "https://app.tidesatglobal.com/vds1/vds1_out.csv",
        "coord": [-30.096215, -51.260051],
        "descricao_imagem": "Estação VDS1 - Guaíba (Vila Assunção)",
        "caminho_imagem": "vds1_photo.jpg",
        "cota_alerta": 1.80,
        "cota_inundacao": 2.50
    },
    "VDS2": {
        "descricao": "VDS2 - Guaíba (Vila Assunção - 2)",
        "url": "https://app.tidesatglobal.com/vds2/vds2_out.csv",
        "coord": [-30.096215, -51.260051], 
        "descricao_imagem": "Estação VDS2 - Guaíba (Vila Assunção - 2)",
        "caminho_imagem": " ",
        "cota_alerta": 1.80,
        "cota_inundacao": 2.50
    }
}

ESTACAO_PADRAO = "SPH4"