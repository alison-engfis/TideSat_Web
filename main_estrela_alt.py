'''
Arquivo que contém todas as informações consideradas constantes
para o funcionamento do fluxo da lógica do script main-alt-estrela.py

'''

################# FUSO PADRÃO #################
TIMEZONE_PADRAO = "America/Sao_Paulo"

################# CONFIGURAÇÕES DE ESTRELA #################
ESTACOES_ESTRELA = {
    "EST1": {
        "descricao": "EST1 - Rio Taquari (Foz do Boa Vista)",
        "url": "https://app.tidesatglobal.com/est1/est1_out.csv",
        "coord": [-29.471768, -51.956703],
        "descricao_imagem": "Estação EST1 - Porto de Estrela",
        "caminho_imagem": "",
        "cota_alerta": 17.00,
        "cota_inundacao": 19.00
    },
    "EST2": {
        "descricao": "EST2 - Rio Taquari (Porto de Estrela)",
        "url": "https://app.tidesatglobal.com/est2/est2_out.csv",
        "coord": [-29.472909, -51.958792],
        "descricao_imagem": "Estação EST2 - Silo do Porto",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    "EST3": {
        "descricao": "EST3 - Centro de Estrela",
        "url": "https://app.tidesatglobal.com/est3/est3_out.csv",
        "coord": [-29.498673, -51.967801],
        "descricao_imagem": "Estação EST3 - Centro de Estrela",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    "EST4": {
        "descricao": "EST4 - Usina Hidrelétrica (Certel)",
        "url": "https://app.tidesatglobal.com/est4/est4_out.csv",
        "coord": [-29.472496, -51.868165],
        "descricao_imagem": "Estação EST4 - Usina Hidrelétrica (Certel)",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    "EST5": {
        "descricao": "EST5 - Cascata Santa Rita",
        "url": "https://app.tidesatglobal.com/est5/est5_out.csv",
        "coord": [-29.519974, -51.903343],
        "descricao_imagem": "Estação EST5 - Cascata Santa Rita",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    },
    "EST6": {
        "descricao": "EST6 - Rio Taquari (Costão)",
        "url": "https://app.tidesatglobal.com/est6/est6_out.csv",
        "coord": [-29.472496, -51.868165],
        "descricao_imagem": "Estação EST6 - Rio Taquari (Costão)",
        "caminho_imagem": " ",
        "cota_alerta": " ",
        "cota_inundacao": " "
    }
        
}

ESTACAO_PADRAO_ESTRELA = "EST1"
