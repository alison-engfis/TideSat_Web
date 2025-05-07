import pandas as pd
import streamlit as st
import requests
from io import StringIO
import plotly.express as px
from datetime import timedelta
import pytz
import base64
import pydeck as pdk

# Utilizando toda a largura da página
st.set_page_config(layout="wide", page_icon="Logo HighRes iniciais2.png",page_title="TideSat", initial_sidebar_state="collapsed")

# CSS's para personalizar a fonte dos seletores
st.markdown(
    """
    <style>
    /* Diminuir tamanho da fonte do seletor de estação */
    .stSelectbox > div[data-baseweb="select"] {
        font-size: 14px !important;
    }

    /* Diminuir tamanho da fonte do seletor de fuso horário */
    .stSelectbox > label {
        font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
    /* Estilo para truncar texto no botão */
    button {
        white-space: nowrap;    /* Impede quebra de linha */
        overflow: hidden;       /* Oculta o texto que ultrapassa */
        text-overflow: ellipsis; /* Adiciona reticências (...) */
    }
    </style>
""", unsafe_allow_html=True)

# Constantes configuráveis
TIMEZONE_PADRAO = "America/Sao_Paulo"
ESTACAO_PADRAO = "SPH4"
ESTACOES = {
    "SPH4": {
        "descricao": "SPH4 - Guaíba (Av. Mauá)",
        "url": "https://app.tidesatglobal.com/sph4/sph4_out.csv",
        "coord": [-30.02703, -51.23166],
        "descricao_imagem": "Estação SPH4 - Guaíba (Av. Mauá)",
        "caminho_imagem": "sph4_photo.jpg"
    },
    "VDS1": {
        "descricao": "VDS1 - Guaíba (Vila Assunção)",
        "url": "https://app.tidesatglobal.com/vds1/vds1_out.csv",
        "coord": [-30.096215, -51.260051],
        "descricao_imagem": "Estação VDS1 - Guaíba (Vila Assunção)",
        "caminho_imagem": "vds1_photo.jpg"
    },
    "VDS2": {
        "descricao": "VDS2 - Guaíba (Vila Assunção - 2)",
        "url": "https://app.tidesatglobal.com/vds2/vds2_out.csv",
        "coord": [-30.096215, -51.260051], 
        "descricao_imagem": "Estação VDS2 - Guaíba (Vila Assunção - 2)",
        "caminho_imagem": " "
    },
    "IDP1": {
        "descricao": "IDP1 - Guaíba (Arquipélago)",
        "url": "https://app.tidesatglobal.com/idp1/idp1_out.csv",
        "coord": [-30.029811, -51.25147],
        "descricao_imagem": "Estação IDP1 - Guaíba (Arquipélago)",
        "caminho_imagem": "idp1_photo.jpg"
    },
    "ITA1": {
        "descricao": "ITA1 - Guaíba (Farol de Itapuã)",
        "url": "https://app.tidesatglobal.com/ita1/ita1_out.csv",
        "coord": [-30.385119, -51.059579],
        "descricao_imagem": "Estação ITA1 - Guaíba (Farol de Itapuã)",
        "caminho_imagem": "ita1_photo.jpg"
    },
    "ACT1": {
        "descricao": "ACT1 - Arroio Cavalhada",
        "url": "https://app.tidesatglobal.com/act1/act1_out.csv",
        "coord": [-30.09157, -51.248928],
        "descricao_imagem": "Estação ACT1 - Arroio Cavalhada",
        "caminho_imagem": " "
    },
    "ADV3": {
        "descricao": "ADV3 - Arroio Dilúvio",
        "url": "https://app.tidesatglobal.com/adv3/adv3_out.csv",
        "coord": [-30.047258, -51.197514],
        "descricao_imagem": "Estação ADV3 - Arroio Dilúvio",
        "caminho_imagem": " "
    },
    "RLS1": {
        "descricao": "RLS1 - Represa (Lomba do Sabão)",
        "url": "https://app.tidesatglobal.com/rls1/rls1_out.csv",
        "coord": [-30.0840741, -51.1110800],
        "descricao_imagem": "Estação RLS1 - Represa (Lomba do Sabão)",
        "caminho_imagem": "rls1_photo.jpg"
    },
    "RIG1": {
        "descricao": "RIG1 - Centro de Rio Grande",
        "url": "https://app.tidesatglobal.com/rig1/rig1_out.csv",
        "coord": [-32.026822, -52.103654],
        "descricao_imagem": "Estação RIG1 - Centro de Rio Grande",
        "caminho_imagem": " "
    },
    "STH1": {
        "descricao": "STH1 - Fábrica Stihl (São Leopoldo)",
        "url": "https://app.tidesatglobal.com/sth1/sth1_out.csv",
        "coord": [-29.787741, -51.109447],
        "descricao_imagem": "Estação STH1 - Fábrica Stihl (São Leopoldo)",
        "caminho_imagem": "STH1_photo.jpg"
    },
    "EST1": {
        "descricao": "EST1 - Porto de Estrela",
        "url": "https://app.tidesatglobal.com/est1/est1_out.csv",
        "coord": [-29.471768, -51.956703],
        "descricao_imagem": "Estação EST1 - Porto de Estrela",
        "caminho_imagem": " "
    }
}
COTAS_NOTAVEIS = {
    "SPH4": {"cota_alerta": 2.50, "cota_inundacao": 3.00},
    "VDS1": {"cota_alerta": 1.80, "cota_inundacao": 2.50},
    "VDS2": {"cota_alerta": 1.80, "cota_inundacao": 2.50},
    "IDP1": {"cota_alerta": 1.85, "cota_inundacao": 2.05},
    "ITA1": {},  # Sem cotas
    "ACT1": {},  # Sem cotas
    "ADV3": {},  # Sem cotas
    "RLS1": {},  # Sem cotas
    "RIG1": {},  # Sem cotas
    "STH1": {},  # Sem cotas
    "EST1": {"cota_alerta": 17.00, "cota_inundacao": 19.00}
}

# Verifica se o fuso horário está definido
if "fuso_selecionado" not in st.session_state:
    st.session_state["fuso_selecionado"] = TIMEZONE_PADRAO  # Valor padrão

# Inicia o estado para o modo de visualização
ms = st.session_state

if "temas" not in ms: 
  ms.temas = {"tema_atual": "escuro",
              "atualizado": True,
              "claro": {
                  "theme.base": "light",
                  "theme.backgroundColor": "#121212",
                  "theme.primaryColor": "#87CEEB",
                  "theme.secondaryBackgroundColor": "#262B36",
                  "theme.textColor": "white",
                  "icone_botoes": "🌞",
                  "cor_linha": "#0065cc",
                  "cor_texto": "#0061c3",
                  "cor_mapa": "#0065cc"
              },
              "escuro":  {
                  "theme.base": "dark",
                  "theme.backgroundColor": "#ffffff",
                  "theme.primaryColor": "#0065cc",
                  "theme.secondaryBackgroundColor": "#e1e4e8",
                  "theme.textColor": "#0a1464",
                  "icone_botoes": "🌜",
                  "cor_linha": "#87CEEB",
                  "cor_texto": "#87CEEB",
                  "cor_mapa": "#87CEEB"
              },
  }

# Verifica e faz o rerun
if ms.temas["atualizado"] == False:
    ms.temas["atualizado"] = True
    st.rerun()  # Use o rerun para evitar um loop infinito

# Cor do tema atual para os detalhes
cor_linha = ms.temas["claro"]["cor_linha"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["cor_linha"]
cor_texto = ms.temas["claro"]["cor_texto"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["cor_texto"]
cor_mapa = ms.temas["claro"]["cor_mapa"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["cor_mapa"]
cor_localizacao = ""

if cor_mapa == ms.temas["claro"]["cor_mapa"]: 

    cor_localizacao = "[0, 101, 204, 255]"

if cor_mapa == ms.temas["escuro"]["cor_mapa"]:

    cor_localizacao = "[135, 206, 235, 200]"

# Cache por 10 minutos
@st.cache_data(ttl=600)
def carregar_dados(url):

    resposta = requests.get(url, verify=False, timeout=10)

  # Interrompe a execução caso o status_code não seja 200
    if resposta.status_code != 200:
        st.error("Erro ao acessar os dados.")
        st.stop()

    dados_nivel = StringIO(resposta.text)
    df = pd.read_csv(dados_nivel, sep=',')

    # Renomeando as colunas
    df.rename(columns={
        '% year': 'year', ' month': 'month', ' day': 'day',
        ' hour': 'hour', ' minute': 'minute', ' second (GMT/UTC)': 'second',
        ' water level (meters)': 'water_level(m)'}, inplace=True)

    # Criando a coluna datetime e definindo o fuso horário UTC
    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
    df['datetime_utc'] = df['datetime'].dt.tz_localize('UTC')

    return df

# Função para filtrar os dados pelo período selecionado
def filtrar_dados(df, dados_inicio, dados_fim, fuso_selecionado):

    # Convertendo dados_inicio e dados_fim para datetime
    dados_inicio_dt = pd.to_datetime(dados_inicio).tz_localize(fuso_selecionado)
    dados_fim_dt = pd.to_datetime(dados_fim).tz_localize(fuso_selecionado)

    filtro = (df['datetime_ajustado'] >= dados_inicio_dt) & (df['datetime_ajustado'] < dados_fim_dt + timedelta(days=1))

    return df.loc[filtro]

# Função do seletor de fuso
def fuso_horário():

    st.markdown("<br>", unsafe_allow_html=True)

    # Lista de todos os fusos horários disponíveis
    fusos = pytz.all_timezones

    _, col_fuso, _ = st.columns([1, 3, 2])

    with col_fuso:

        # Título centralizado acima do seletor
        st.markdown("""
                <div style='text-align: center;'>
                    <p style='font-size: 14px; margin: 0;'>Fuso horário</span></p>
                </div>
                """, unsafe_allow_html=True)

        # Seletor de fuso horário
        fuso_selecionado = st.selectbox(" ", fusos, label_visibility='collapsed', key='fuso_selecionado')

    return fuso_selecionado

# Função para formatar o nível recente via mediana
def nivel_recente(df, fuso_selecionado):

    # Define o limite de tempo para as últimas 6 horas
    limite_tempo = df["datetime_utc"].max() - timedelta(hours=6)
    ultimas_6h = df[df["datetime_utc"] >= limite_tempo]

    # Caso não hajam dados suficientes
    if ultimas_6h.empty:

        # Interrompe a execução caso os dados não sejam suficientes para a mediana de 6h.
        st.stop()

    # Calcula o nível mediano e a data/hora da última medida
    nivel_mediana = ultimas_6h["water_level(m)"].median()
    dh_ultima = ultimas_6h["datetime_utc"].max().tz_convert(fuso_selecionado)

    # Formata o nível com vírgula, incluindo a unidade de medida e a data/hora
    nivel_formatado = f"{nivel_mediana:.2f}&nbsp;m".replace('.', ',')
    dh_ultima_formatada = dh_ultima.strftime('%d/%m/%Y - %H:%M')

    return nivel_formatado, dh_ultima_formatada

# Função para exibir as cotas notáveis nos filtros
def cotas_notaveis(estacao_selecionada):

    # Recupera as cotas notáveis para a estação selecionada
    cotas = COTAS_NOTAVEIS.get(estacao_selecionada, {})
    cota_alerta = cotas.get("cota_alerta")
    cota_inundacao = cotas.get("cota_inundacao")

    return cota_alerta, cota_inundacao

# Função para plotar o gráfico
def plotar_grafico(dados_filtrados, estacao_selecionada, cota_alerta, cota_inundacao, dados_inicio, dados_fim):

    if dados_filtrados is None or dados_filtrados.empty:
        st.write(f"Nenhum dado encontrado para o período selecionado na estação {estacao_selecionada}.")
        st.stop()

    # Criação do gráfico interativo
    fig = px.line(
        dados_filtrados,
        render_mode='svg',
        x='datetime_ajustado',
        y='water_level(m)',
        labels={'datetime_ajustado': 'Data', 'water_level(m)': 'Nível (m)'}
    )

    # Configurações dos eixos
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    # Configurações do layout
    fig.update_layout(
        xaxis_title={'font': {'size': 20}},
        yaxis_title={'font': {'size': 20}},
        font={'size': 18},
        height=450,
        width=1000,
        margin=dict(l=40, r=0.1, t=40, b=40)
    )

    # Ajuste da cor da linha principal
    fig.update_traces(line=dict(color=cor_linha))

    if cota_inundacao:
            fig.add_shape(
            legendrank=1,
            showlegend=True,
            type="line",
            xref="x",
            line=dict(color="#FF0000", dash="dash"),
            name="Cota de inundação",
            x0=dados_inicio,
            x1=dados_fim,
            y0=cota_inundacao,
            y1=cota_inundacao,
        )
            
    # Adiciona as cotas notáveis, se necessário
    if cota_alerta:
            fig.add_shape(
            legendrank=1,
            showlegend=True,
            type="line",
            xref="x",
            line=dict(color="#FFA500", width=2, dash="dash"),
            name="Cota de alerta",
            x0=dados_inicio,
            x1=dados_fim,
            y0=cota_alerta,
            y1=cota_alerta,
            )        
            
    # Exibe o gráfico
    st.plotly_chart(fig, use_container_width=True)

# Função para converter a imagem para base64
def converter_base64(caminho_imagem):

    try:
        
        with open(caminho_imagem, "rb") as file:
            link = base64.b64encode(file.read()).decode()

        return link
        
    except Exception as e:

        print(f"Erro ao converter imagem: {e}")

        return None

# Função para configurar a imagem e o mapa da estação selecionada
def imagem_mapa_estacao(estacao_nome):

    _, col_img_estac, _, col_mapa, _ = st.columns([0.1, 2, 0.5, 4, 0.9])

    with col_img_estac:

        # Moldura para a foto da estação
        with st.container(border=True):

            # Obtém os dados da estação selecionada
            estacoes_info = ESTACOES
            estacao = estacoes_info.get(estacao_nome)

            if estacao:
                
                imagem = estacao.get("caminho_imagem")
                descricao_imagem = estacao.get("descricao_imagem")

                # Converte a imagem para base64
                img_estac_base64 = converter_base64(imagem)

                if img_estac_base64:

                    # HTML e CSS para permitir expansão da imagem
                    expansivel_code = f"""
                    <style>
                        .img-expansivel {{
                            transition: transform 0.2s ease-in-out;
                            cursor: zoom-in;
                            object-fit: contain;
                            max-width: 100%;
                            height: auto;
                        }}
                        .img-expansivel:active {{
                            transform: scale(1.6); /* Aumenta a imagem */
                            cursor: zoom-out;
                        }}
                    </style>
                    <div style="display: flex; justify-content: center; align-items: center;">
                        <img src='data:image/jpeg;base64,{img_estac_base64}' alt="{descricao_imagem}" 
                            title="{descricao_imagem}" class="img-expansivel">
                    </div>
                    """
                    # Exibe o código HTML no Streamlit
                    st.markdown(expansivel_code, unsafe_allow_html=True)

                    st.markdown("""
                    <div style='text-align: center;'>
                        <p style='font-size: 20px; margin: 0;'> </span></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Exibe mensagem alternativa se a imagem não for encontrada
                    st.warning(f"Imagem não disponível para {estacao_nome}.")

    with col_mapa:
        
        # Moldura para o mapa
        with st.container(border=True):
            # Obtém os dados da estação selecionada
            estacao = ESTACOES.get(estacao_nome)

            if estacao:
                latitude = estacao["coord"][0]
                longitude = estacao["coord"][1]

                # Configuração do PyDeck
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"latitude": latitude, "longitude": longitude}]),
                    get_position="[longitude, latitude]",
                    get_radius=90,  # Ajustar tamanho do ponto
                    get_fill_color=cor_localizacao,
                    pickable=True,  # Habilitar clique nos pontos
                )

                # Visão inicial do mapa
                view_state = pdk.ViewState(
                    latitude=latitude,
                    longitude=longitude,
                    zoom=13.8,
                    pitch=0
                )

                # Mostra o mapa interativo
                tooltip = {"html": f"<b>{estacao['descricao']}</b>", "style": {"color":cor_mapa}}
                deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)

                # Exibe o mapa em um espaço limitado
                st.markdown("<div style='height: 10px;'>", unsafe_allow_html=True)  # Define a altura
                st.pydeck_chart(deck, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)    

# Função para mudar o tema
def MudarTema():

    tema_anterior = ms.temas["tema_atual"]
    tdict = ms.temas["claro"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]
    
    for chave, valor in tdict.items(): 

        if chave.startswith("theme"): 
            st._config.set_option(chave, valor)

    ms.temas["atualizado"] = False

    if tema_anterior == "escuro": 
        ms.temas["tema_atual"] = "claro"

    elif tema_anterior == "claro": 
        ms.temas["tema_atual"] = "escuro"

# Função para o seletor de modo de visualização
def modo_visualizacao():

    st.markdown("<br>", unsafe_allow_html=True)

    _, col_txt_visual, _ = st.columns([1, 3.5, 1])

    with col_txt_visual:

        # Título centralizado acima do seletor
        st.markdown("""
            <div style='text-align: center;'>
                <p style='font-size: 14px; margin: 0;'>Modo de&nbsp; visualização</span></p>
            </div>
            """, unsafe_allow_html=True)
        
    _, col_visual, _ = st.columns([1.25, 1, 1])

    with col_visual:   

        # Botão para alternar o tema
        icone_botoes = ms.temas["claro"]["icone_botoes"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["icone_botoes"]
        st.button(icone_botoes, on_click=MudarTema)

# Função para construir o layout
def construir_layout():

    # Ocultando menu e rodapé (via CSS)
    esconder = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stActionButton {display: none;}
        </style>
        """
    st.markdown(esconder, unsafe_allow_html=True)

    with st.container(border=True):

        # Duas colunas principais
        col_filtros, col_grafico, _ = st.columns([1, 2.15, 0.1])

        # Container com os filtros da primeira coluna
        with col_filtros:

            with st.container():

                _, col_img, _ = st.columns([0.5, 2, 1.4])

                with col_img:
                    # Logo TideSat com link
                    caminho_imagem = "TideSat_logo.webp"
                    imagem_base64 = converter_base64(caminho_imagem)

                    html = f"""
                        <div style='text-align: center;'>
                            <a href='https://tidesatglobal.com' target='_blank'>
                                <img src='data:image/webp;base64,{imagem_base64}' width='200'>
                            </a>
                        </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                _, col_estacao, _ = st.columns([0.45, 2, 1.35])

                with col_estacao:

                    # Título centralizado acima do seletor
                    st.markdown("""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>Estação de medição</span></p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Seletor de estações
                    estacao_selecionada = st.selectbox(" ", list(ESTACOES.keys()), 
                                                    format_func=lambda code :ESTACOES[code]["descricao"],
                                                    index=list(ESTACOES.keys()).index(ESTACAO_PADRAO),
                                                    label_visibility='collapsed')

                    # Armazenando no estado da sessão
                    st.session_state["estacao_selecionada"] = estacao_selecionada

                    estacao_info = ESTACOES[estacao_selecionada]
                    url_estacao = estacao_info["url"]

                    dados = carregar_dados(url_estacao)
                    dados['datetime_ajustado'] = dados['datetime_utc'].dt.tz_convert(st.session_state["fuso_selecionado"])

                    # Salvando os dados ajustados no estado da sessão
                    st.session_state["dados_estacao"] = dados

                    dados_inicio = dados['datetime_ajustado'].min().date()
                    dados_fim = dados['datetime_ajustado'].max().date()

                # Seleção de datas e botões rápidos
                _, col_inicio, col_fim, _ = st.columns([0.46, 1, 1, 1.37])

                with col_inicio:

                    st.markdown("""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>Data inicial</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    st.session_state["dados_inicio"] = st.date_input(" ", value=dados_inicio, format="DD/MM/YYYY", label_visibility='collapsed')

                with col_fim:

                    st.markdown("""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>Data final</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                    st.session_state["dados_fim"] = st.date_input(" ", value=dados_fim, format="DD/MM/YYYY", label_visibility='collapsed')

                _, col_inteiro, col_sete, _ = st.columns([0.46, 1, 1, 1.33])

                with col_inteiro:

                    if st.button('Período inteiro', use_container_width=True):
                        st.session_state["dados_inicio"] = dados_inicio
                        st.session_state["dados_fim"] = dados_fim

                with col_sete:

                    if st.button('Últimos 7 dias', use_container_width=True):
                        st.session_state["dados_inicio"] = (dados['datetime_ajustado'].max() - timedelta(days=7)).date()
                        st.session_state["dados_fim"] = dados['datetime_ajustado'].max().date()

                # Informação do nível recente
                _, col_recente, _ = st.columns([0.45, 2, 1.33])

                with col_recente:

                    df_nivel = carregar_dados(url_estacao)
                    nivel_formatado, dh_ultima_formatada = nivel_recente(df_nivel, st.session_state["fuso_selecionado"])

                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 20px; margin: 0;'>Nível recente: <span style='color:{cor_texto};'>{nivel_formatado}</span></p>
                        <div style='text-align: center;'>
                            <p style='font-size: 15px; margin: 0;'>Atualização: {dh_ultima_formatada}</p>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)        

        # Coluna para gráfico
        with col_grafico:

            with st.container():

                dados_filtrados = filtrar_dados(
                    st.session_state["dados_estacao"], st.session_state["dados_inicio"],
                    st.session_state["dados_fim"],st.session_state["fuso_selecionado"])
                
                cota_alerta, cota_inundacao = cotas_notaveis(estacao_selecionada)

                # Plota o gráfico com as cotas, se aplicável
                plotar_grafico(dados_filtrados, estacao_selecionada, cota_alerta, cota_inundacao, st.session_state["dados_inicio"], st.session_state["dados_fim"])

                st.markdown("<br>", unsafe_allow_html=True)

                # Mostra a imagem da estação selecionada
                imagem_mapa_estacao(estacao_selecionada)

    _, col_modo, col_fuso, _ = st.columns([2.5, 1, 2, 2])    

    with col_modo:

        modo_visualizacao()  

    with col_fuso:
            
        fuso_horário()            

# Função principal
def main():

    construir_layout()

# Executa a função principal
if __name__ == "__main__":
    main()
