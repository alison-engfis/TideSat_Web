'''
Arquivo que contém todas as ferramentas comuns tanto a main-alt.py, 
como a main-estrela-alt.py e main-barroso.py. Ou seja, são funções base  
para o correto funcionamento de ambos os scripts.

'''

from datetime import timedelta
import requests
import base64
import streamlit as st
from io import StringIO
import plotly.express as px
import pydeck as pdk
import pandas as pd
import pytz
import hmac 
import numpy as np

from main_config import TIMEZONE_PADRAO 

# Verifica se o fuso horário está definido
if "fuso_selecionado" not in st.session_state:
    st.session_state["fuso_selecionado"] = TIMEZONE_PADRAO  # Valor padrão   

# Função para configurar a autenticação por senha (para tidesat-barroso)
def checar_senha(lang):
    if st.session_state.get("senha_correta", False):
        return True  # Senha já validada anteriormente

    def senha():
        if "senha" not in st.session_state:
            return

        if hmac.compare_digest(st.session_state["senha"], st.secrets["password"]["value"]):
            st.session_state["senha_correta"] = True
            del st.session_state["senha"]  # Remove a senha da sessão
        else:
            st.session_state["senha_correta"] = False

    _, col_senha, _ = st.columns([1, 1, 1])

    with col_senha:
        st.text_input("Senha de acesso", type="password", on_change=senha, key="senha")

        if "senha_correta" in st.session_state and not st.session_state["senha_correta"]:
            st.error(f"{lang['incorrect_password']}")

        return False
    
# Função para restaurar o estado (estação e período)
def restaurar_estado():
    if st.session_state.get("atualizar_tema", False):
        st.session_state["atualizar_tema"] = False  # Resetamos o flag para evitar loop infinito

        # Restaura a estação e o período salvos temporariamente
        if "estacao_selecionada_temp" in st.session_state:
            st.session_state["estacao_selecionada"] = st.session_state.pop("estacao_selecionada_temp")

        if "ultimo_periodo_temp" in st.session_state:
            st.session_state["ultimo_periodo"] = st.session_state.pop("ultimo_periodo_temp")     

# Função que configura o layout principal
def configurar_layout():

    obter_tema()

    st.set_page_config(layout="wide", page_icon="Logo HighRes iniciais2.png",page_title="TideSat", initial_sidebar_state="collapsed")

    # CSS's para personalizar a fonte dos seletores
    st.markdown(
        """
        <style>
        /* Diminuir tamanho da fonte do seletor de estação */
        .stSelectbox > div[data-baseweb="select"] {
            font-size: 13px !important;
        }

        /* Diminuir tamanho da fonte do seletor de fuso horário */
        .stSelectbox > label {
            font-size: 13px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # CSS para personalizar e evitar a quebra de linhas nos botões
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

    # CSS para reduzir o espaçamento superior da página
    st.markdown("""
        <style>
        .block-container {
            padding-top: 0rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Ocultando menu e rodapé (via CSS)
    esconder = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stActionButton {display: none;}
        </style>
        """
    st.markdown(esconder, unsafe_allow_html=True)

# Função que coordena o seguinte: Se NÃO for o logo da TideSat, mostramos o "Powered by TideSat"
def mostrar_cabecalho_tidesat(logotipo):
    
    if logotipo not in ["TideSat_logo.webp", "Logo HighRes iniciais2.png"]:
        _, col_cabecalho, _ = st.columns([1, 4, 1])

        with col_cabecalho:
            # Converte logo TideSat para base64
            caminho_imagem = "TideSat_logo.webp"
            imagem_base64 = converter_base64(caminho_imagem)

            # HTML para alinhar "Powered by" e o logo lado a lado
            html = f"""
                <div style='display: flex; justify-content: center; align-items: center; gap: 8px;'>
                    <span style='font-size: 16px; font-style: italic; font-weight: bold; color: gray;'>POWERED BY</span>
                    <a href="https://www.tidesatglobal.com/" target="_blank">
                        <img src='data:image/webp;base64,{imagem_base64}' width='100'>
                    </a>
                </div>
            """
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

# Função para carregar os dados dos links
def carregar_dados(url):
        
        # Fazendo a requisição dos dados
        resposta = requests.get(url, verify=False, timeout=100)

        # Verifica se a requisição foi bem-sucedida
        if resposta.status_code != 200:
            st.markdown("<br>" * 2, unsafe_allow_html=True)
            st.warning("Erro ao acessar os dados da estação selecionada.")
            st.stop()

        # Carregando os dados no DataFrame
        dados_nivel = StringIO(resposta.text)
        df = pd.read_csv(dados_nivel, sep=',')

        # Verifica se o DataFrame está vazio
        if df.empty:
            st.markdown("<br>" * 2, unsafe_allow_html=True)
            st.warning("Erro ao carregar os dados da estação selecionada.")
            st.stop()

        # Renomeia as colunas conforme necessário
        df.rename(columns={
            '% year': 'year', ' month': 'month', ' day': 'day',
            ' hour': 'hour', ' minute': 'minute', ' second (GMT/UTC)': 'second',
            ' water level (meters)': 'water_level(m)'}, inplace=True)

        # Converte a data para o formato datetime
        df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])

        # Adiciona a coluna de data UTC
        df['datetime_utc'] = df['datetime'].dt.tz_localize('UTC')

        return df

# Retorna uma cópia do DataFrame sem a última hora de dados (evitar o chicoteamento)
def corte_ultima_1h(df):

    limite = df['datetime_utc'].max() - pd.Timedelta(hours=1)
    return df[df['datetime_utc'] <= limite]

# Função do seletor de fuso
def fuso_horario(lang):

    # Lista de todos os fusos horários disponíveis
    fusos = pytz.all_timezones

    # Verifica se há um fuso horário armazenado no session_state
    if "fuso_selecionado" not in st.session_state:
        st.session_state["fuso_selecionado"] = TIMEZONE_PADRAO  # Define o fuso padrão apenas na inicialização

    fuso_atual = st.session_state["fuso_selecionado"]

    _, col_fuso, _ = st.columns([0.3, 1, 0.3])

    with col_fuso:
        # Usando expander para esconder ou mostrar o seletor com fuso atual
        with st.expander(f"{lang['timezone']}: {fuso_atual}", expanded=False):
            
            # Seletor de fuso horário dentro do expander
            fuso_selecionado = st.selectbox(
                " ", 
                fusos, 
                index=fusos.index(fuso_atual),  # Mantém o índice correto
                label_visibility='collapsed', 
                key="fuso_selecionado"  # Vincula ao session_state
            )

    return fuso_selecionado

# Função que calcula o nível recente (levando em conta os ajustes para o cálculo de velocidade)
def nivel_recente(df, fuso_selecionado, lang, modo="mediana"):

    # Define o limite de tempo para as últimas 6 horas
    limite_tempo = df["datetime_utc"].max() - timedelta(hours=6)
    ultimas_6h = df[df["datetime_utc"] >= limite_tempo]

    if ultimas_6h.empty or len(ultimas_6h) < 2:
        return "Indisp.", "Indisp."

    # Ajusta o horário da última medição para o fuso selecionado
    dh_ultima = ultimas_6h["datetime_utc"].max().tz_convert(fuso_selecionado)

    if modo == "ajustado":

        agora_utc = pd.Timestamp.utcnow()
        
        ultimas_6h["delta_horas"] = (ultimas_6h["datetime_utc"] - agora_utc).dt.total_seconds() / 3600

        x = ultimas_6h["delta_horas"].values
        y = ultimas_6h["water_level(m)"].values

        coef = np.polyfit(x, y, deg=1)

        inclinacao = coef[0]  # velocidade m/h
        nivel_ajustado = coef[1]  # valor no instante atual (t=0)
        nivel_formatado = f"{nivel_ajustado:.2f}&nbsp;m".replace('.', ',')

    else:
        nivel_mediana = ultimas_6h["water_level(m)"].median()
        nivel_formatado = f"{nivel_mediana:.2f}&nbsp;m".replace('.', ',')

    if lang["lang_code"] == "en":
        dh_ultima_formatada = dh_ultima.strftime('%m/%d/%Y - %I:%M %p')

    else:
        dh_ultima_formatada = dh_ultima.strftime('%d/%m/%Y - %H:%M')

    return nivel_formatado, dh_ultima_formatada

#Função que calcula a velocidade de variação recente
def calcular_velocidade(df):

    agora_utc = pd.Timestamp.utcnow()
    limite_6h = agora_utc - pd.Timedelta(hours=6)
    df_filtrado = df[df["datetime_utc"] >= limite_6h]

    if df_filtrado.empty or len(df_filtrado) < 2:
        return "Indisp."

    df_filtrado["delta_horas"] = (df_filtrado["datetime_utc"] - agora_utc).dt.total_seconds() / 3600
    x = df_filtrado["delta_horas"].values
    y = df_filtrado["water_level(m)"].values
    coef = np.polyfit(x, y, deg=1)
    inclinacao = coef[0]

    return f"{inclinacao:+.2f} m/h".replace('.', ',')

# Verifica o status de funcionamento da estação com base na última medição
def verificar_status_estacao(ultimo_registro_utc):

    limite_inatividade = pd.Timestamp.utcnow() - pd.Timedelta(hours=12)

    return "Ativa" if ultimo_registro_utc > limite_inatividade else "Inativa"

# Função para exibir as cotas notáveis nos filtros
def cotas_notaveis(estacao_nome, estacoes_info):

    # Recupera as cotas notáveis para a estação selecionada
    cotas = estacoes_info.get(estacao_nome, {})
    cota_alerta = cotas.get("cota_alerta")
    cota_inundacao = cotas.get("cota_inundacao")

    return cota_alerta, cota_inundacao

# Função para determinar a situação atual do nível da estação com base nas cotas
def situacao_nivel(nivel, cota_alerta, cota_inundacao):

    if cota_alerta in ("", " ", None) or cota_inundacao in ("", " ", None):

        return "Indisponível", "gray"
    
    elif nivel < cota_alerta:
        return "Normal", "green"
    
    elif cota_alerta <= nivel < cota_inundacao:
        return "Alerta", "orange"
    
    else:
        return "Inundação", "red"
    
# Função para converter a imagem para base64
def converter_base64(caminho_imagem):

    try:
        
        with open(caminho_imagem, "rb") as file:
            link = base64.b64encode(file.read()).decode()

        return link
        
    except Exception as e:

        print(f"Erro ao converter imagem: {e}")

        return None

# Função para configurar a imagem da estação selecionada
def exibir_imagem_estacao(estacao):

    imagem = estacao.get("caminho_imagem")
    descricao_imagem = estacao.get("descricao_imagem")

    # Converte a imagem para base64
    img_estac_base64 = converter_base64(imagem)

    if img_estac_base64:
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
                transform: scale(1.6);
                cursor: zoom-out;
            }}
        </style>
        <div style="display: flex; justify-content: center; align-items: center;">
            <img src='data:image/jpeg;base64,{img_estac_base64}' alt="{descricao_imagem}" 
                 title="{descricao_imagem}" class="img-expansivel">
        </div>
        """
        st.markdown(expansivel_code, unsafe_allow_html=True)
    else:
        st.warning("Imagem não disponível.")

# Função para configurar o mapa da estação selecionada
def exibir_mapa_estacao(estacao):
    _, _, cor_mapa, cor_localizacao, _ = obter_tema()

    if estacao and "coord" in estacao:
        latitude = estacao["coord"][0]
        longitude = estacao["coord"][1]

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame([{"latitude": latitude, "longitude": longitude}]),
            get_position="[longitude, latitude]",
            get_radius=90,
            get_fill_color=cor_localizacao,
            pickable=True
        )

        view_state = pdk.ViewState(
            latitude=latitude,
            longitude=longitude,
            zoom=13.8,
            pitch=0
        )

        tooltip = {"html": f"<b>{estacao.get('descricao')}</b>", "style": {"color": cor_mapa}}

        deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)

        st.pydeck_chart(deck, use_container_width=True)   

# Função que configura a exibição do gráfico
def plotar_grafico(url, estacoes_info, dados_filtrados, estacao_selecionada, cota_alerta, cota_inundacao, dados_inicio, dados_fim, lang):
    
    cor_linha, _, _, _, _ = obter_tema()

    if dados_filtrados is None or dados_filtrados.empty:
        st.write(f"Nenhum dado encontrado para o período selecionado na estação {estacao_selecionada}.")
        st.stop()

    # Criação do gráfico interativo
    fig = px.line(
        dados_filtrados,
        render_mode='svg',
        x='datetime_ajustado',
        y='water_level(m)',
        labels={'datetime_ajustado': "Data" if lang["lang_code"] == "pt" else "Date", 'water_level(m)': "Nível (m)" if lang["lang_code"] == "pt" else "Water level (m)"}
    )
    # Configurações dos eixos
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    # Condição para aplicar o ajuste no eixo Y apenas se o período for "Últimas 24h"
    if (dados_fim - dados_inicio) == pd.Timedelta(hours=24):
        
        med = np.median(dados_filtrados['water_level(m)'])
        tempmin = med - 0.5
        tempmax = med + 0.5
        fig.update_yaxes(autorangeoptions_clipmin=tempmin, autorangeoptions_clipmax=tempmax, fixedrange=True)

    elif (dados_fim - dados_inicio) >= pd.Timedelta(days=7):  # Inclui Período Inteiro

        from main_estrela_config import ESTACOES_ESTRELA

        # Verifica se está rodando no app de Estrela
        if estacoes_info == ESTACOES_ESTRELA:

            # Usa os limites globais de EST1
            df_est1 = carregar_dados(ESTACOES_ESTRELA["EST1"]["url"])

            if estacao_selecionada != "EST1":
                
                max_nivel = 21
                min_nivel = df_est1['water_level(m)'].min()
            else:
                max_nivel = df_est1["water_level(m)"].max()
                min_nivel = df_est1["water_level(m)"].min()

        else:
            # Comportamento padrão
            df = carregar_dados(url)
            max_nivel = df['water_level(m)'].max()
            min_nivel = df['water_level(m)'].min()

        # Aplica o range do eixo Y diretamente
        fig.update_yaxes(range=[min_nivel, max_nivel], fixedrange=True)

    fig.update_layout(
        xaxis_title={'font': {'size': 20}},
        yaxis_title={'font': {'size': 20}},
        font={'size': 18},
        height=430,
        margin=dict(l=40, r=0.1, t=40, b=40),
        legend=dict(
            orientation='v',
            yanchor='bottom',
            y=1.01,
            xanchor='left',
            x=0.04,
            font=dict(size=11),
        ),
        autosize=True, 
    )

    # Ajuste da cor da linha principal
    fig.update_traces(line=dict(color=cor_linha))

    # Adiciona a cota de inundação, se disponível
    if cota_inundacao not in (None, "", " "):
        fig.add_shape(
            type="line",
            xref="paper",  
            yref="y",
            x0=0,
            x1=1,
            y0=cota_inundacao,
            y1=cota_inundacao,
            line=dict(color="#FF0000", dash="dash"),
            name = "Cota de inundação" if lang["lang_code"] == "pt" else "Flood level",
            legendgroup="cota_inundacao", 
            showlegend=True  
        )

    # Adiciona a cota de alerta, se disponível
    if cota_alerta not in (None, "", " "):
        fig.add_shape(
            type="line",
            xref="paper",  
            yref="y",
            x0=0,
            x1=1,
            y0=cota_alerta,
            y1=cota_alerta,
            line=dict(color="#FFA500", dash="dash"),
            name="Cota de alerta" if lang["lang_code"] == "pt" else "Alert level",
            legendgroup="cota_alerta",  
            showlegend=True  
        )

    config = {
        "scrollZoom": True,
        "responsive": True,
        "displaylogo": False
    }

    # Exibe o gráfico
    st.plotly_chart(fig, use_container_width=True, config=config)

# Função que configura a exibição do gráfico de sobreposição (exclusivo para tidesat-estrela)
def plotar_sobreposicao_estrela(estacoes_info, lang):

    # Pega o fuso e o período selecionado
    fuso = st.session_state["fuso_selecionado"]
    data_inicio = st.session_state["dados_inicio"]
    data_fim = st.session_state["dados_fim"]

    estacoes_alvo = ["EST1", "EST2", "EST3", "EST6"]

    tracos = []
    todos_valores = []

    cor_linha_padrao, _, _, _, _ = obter_tema()

    cores = {
        "EST2": "blue",
        "EST3": "green",
        "EST6": "red"
    }
    for cod in estacoes_alvo:

        est = estacoes_info.get(cod)

        if not est:

            continue

        try:

            df = carregar_dados(est["url"])
            df['datetime_ajustado'] = df['datetime_utc'].dt.tz_convert(fuso)
            df_filtrado = filtrar_dados(df, data_inicio, data_fim, fuso)

            todos_valores.extend(df_filtrado["water_level(m)"].tolist())

            cor = cores.get(cod, cor_linha_padrao)

            tracos.append(go.Scatter(
                x=np.array(df_filtrado["datetime_ajustado"]),
                y=df_filtrado["water_level(m)"],
                mode='lines',
                name=est["descricao"],
                line=dict(color=cor, width=2)
            ))

        except Exception as e:
            st.warning(f"Erro ao carregar dados de {cod}: {e}")

    if not tracos:
        st.error("Nenhum dado foi carregado para as estações selecionadas.")
        return

    # Eixo Y: ajuste para últimos 24h ou período total
    y_range = None
    delta_periodo = pd.to_datetime(data_fim) - pd.to_datetime(data_inicio)

    if delta_periodo == timedelta(hours=24):
        
       val_min = min(todos_valores)
       val_max = max(todos_valores)
       y_range = [max(0, val_min - 0.5), val_max + 0.5]

    elif delta_periodo >= timedelta(days=7):

        y_range = [min(todos_valores), max(todos_valores)]

    fig = go.Figure(data=tracos)

    fig.update_layout(
        xaxis_title="Data" if lang["lang_code"] == "pt" else "Date",
        yaxis_title="Nível (m)" if lang["lang_code"] == "pt" else "Water level (m)",
        font={'size': 18},
        height=430,
        margin=dict(l=40, r=0.1, t=40, b=40),
        legend=dict(
            orientation='v',
            yanchor='bottom',
            y=1.01,
            xanchor='left',
            x=0.04,
            font=dict(size=11),
        )
    )

    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    if y_range:
        fig.update_yaxes(range=y_range, fixedrange=True)

    config = {
        "scrollZoom": True,
        "responsive": True,
        "displaylogo": False
    }

    st.plotly_chart(fig, use_container_width=True, config=config)

# Função para obter as configurações do tema
def obter_tema():
    ms = st.session_state

    if "temas" not in ms:
        ms.temas = {
            "tema_atual": "claro",
            "atualizado": True,
            "claro": {
                "theme.base": "light",
                "theme.backgroundColor": "#121212",
                "theme.primaryColor": "#87CEEB",
                "theme.secondaryBackgroundColor": "#262B36",
                "theme.textColor": "white",
                "icone_botoes": "Claro",
                "cor_linha": "#0065cc",
                "cor_texto": "#0061c3",
                "cor_mapa": "#0065cc"
            },
            "escuro": {
                "theme.base": "dark",
                "theme.backgroundColor": "#ffffff",
                "theme.primaryColor": "#0065cc",
                "theme.secondaryBackgroundColor": "#e1e4e8",
                "theme.textColor": "#0a1464",
                "icone_botoes": "Escuro",
                "cor_linha": "#87CEEB",
                "cor_texto": "#87CEEB",
                "cor_mapa": "#87CEEB"
            },
        }

    # Cor do tema atual para os detalhes
    cor_linha = ms.temas["claro"]["cor_linha"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["cor_linha"]
    cor_texto = ms.temas["claro"]["cor_texto"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["cor_texto"]
    cor_mapa = ms.temas["claro"]["cor_mapa"] if ms.temas["tema_atual"] == "claro" else ms.temas["escuro"]["cor_mapa"]
    cor_localizacao = ""

    if cor_mapa == ms.temas["claro"]["cor_mapa"]: 
        cor_localizacao = "[0, 101, 204, 255]"

    if cor_mapa == ms.temas["escuro"]["cor_mapa"]:
        cor_localizacao = "[135, 206, 235, 200]"

    return cor_linha, cor_texto, cor_mapa, cor_localizacao, ms

# Função para mudar o tema
def MudarTema():

    _, _, _, _, ms = obter_tema()

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
def modo_visualizacao(lang):

    _, _, _, _, ms = obter_tema()

    # Determina o ícone do botão baseado no tema atual
    icone_id = (
        ms.temas["claro"]["icone_botoes"]
        if ms.temas["tema_atual"] == "claro"
        else ms.temas["escuro"]["icone_botoes"]
    )

    # Tradução dinâmica baseada no idioma
    if lang["lang_code"] == "pt":
        icone_botoes = icone_id  
    
    elif lang["lang_code"] == "en":
        icone_botoes = "Light" if icone_id == "Claro" else "Dark"
    
    else:
        icone_botoes = icone_id  # fallback

    _, col_visual, _ = st.columns([0.5, 1, 0.5])

    with col_visual:

        # Usando um expander para o seletor de modo de visualização

        with st.expander(f"{lang['theme']}: {icone_botoes}", expanded=False):

            # Botão para alternar o tema
            st.button(icone_botoes, on_click=MudarTema)

# Função para construir o layout
def main(estacoes_info, estacao_padrao, logotipo, html_logo, lang): 

    configurar_layout()

    # Mostra cabeçalho "Powered by TideSat" só se for uma dashboard personalizada
    mostrar_cabecalho_tidesat(logotipo)

    tz_padrao = TIMEZONE_PADRAO

    if "fuso_selecionado" not in st.session_state:
        st.session_state["fuso_selecionado"] = tz_padrao

    with st.container(border=True):

        _, col_filtros, _, col_grafico, _ = st.columns([0.1, 1.1, 0.1, 3, 0.1], gap="small", vertical_alignment="top")

        _, cor_texto, _, _, _ = obter_tema()

        with col_filtros:

            with st.container():

                col_img = st.columns([1])[0]

                with col_img:

                    caminho_imagem = logotipo
                    imagem_base64 = converter_base64(caminho_imagem)
                    html = f"""
                        <div style='text-align: center;'>
                            <a href={html_logo} target='_blank'>
                                <img src='data:image/webp;base64,{imagem_base64}' width='250'>
                            </a>
                        </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                col_estacao = st.columns([1])[0]

                with col_estacao:

                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>{lang['station']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    estacao_selecionada = st.selectbox(" ", list(estacoes_info.keys()), 
                                                    format_func=lambda code :estacoes_info[code]["descricao"],
                                                    index=list(estacoes_info.keys()).index(estacao_padrao),
                                                    label_visibility='collapsed')
                   
                    
                    st.session_state["estacao_selecionada"] = estacao_selecionada

                    estacao_info = estacoes_info[estacao_selecionada]

                    url_estacao = estacao_info["url"]

                    dados = carregar_dados(url_estacao)
                    dados['datetime_ajustado'] = dados['datetime_utc'].dt.tz_convert(st.session_state["fuso_selecionado"])
                    
                    st.session_state["dados_estacao"] = dados
                    
                    dados_inicio = dados['datetime_ajustado'].min().date()
                    dados_fim = dados['datetime_ajustado'].max().date()

                    # Limita o início ao primeiro dado da EST6, apenas para o app de Estrela
                    from main_estrela_config import ESTACOES_ESTRELA
                    
                    if estacoes_info == ESTACOES_ESTRELA:
                        try:
                            df_est6 = carregar_dados(ESTACOES_ESTRELA["EST6"]["url"])
                            df_est6["datetime_ajustado"] = df_est6["datetime_utc"].dt.tz_convert(st.session_state["fuso_selecionado"])
                            inicio_est6 = df_est6["datetime_ajustado"].min().date()

                            # Só ajusta se estiver iniciando com o período total (primeira execução)
                            if dados_inicio < inicio_est6:
                                dados_inicio = inicio_est6

                        except Exception as e:
                            st.warning(f"Não foi possível ajustar a data inicial com base na EST6: {e}")

                    if pd.isna(dados_inicio) or pd.isna(dados_fim):
                        st.warning("A estação selecionada ainda não possui dados suficientes para exibição.")
                        st.stop()

                col_situacao = st.columns([1])[0]

                with col_situacao:

                    # Obtém o último dado da estação selecionada
                    ultimo_dado = dados["datetime_utc"].max()
                    status_estacao = verificar_status_estacao(ultimo_dado)

                    # Define cor visual do status
                    cor_status = "green" if status_estacao == "Ativa" else "red"

                    # Tradução para multilíngue
                    texto_status = "Status:" if lang["lang_code"] == "pt" else "Station status:"
                    valor_status = status_estacao if lang["lang_code"] == "pt" else ("Active" if status_estacao == "Ativa" else "Inactive")

                    # Exibe o status
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 20px; margin: 0;'>
                                {texto_status}
                            <span style='font-weight: bold; color: {cor_status};'>{valor_status}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    
                st.markdown("<br>" * 2, unsafe_allow_html=True) 
                
                

                col_inicio, col_fim = st.columns(2, gap="small")

                formato_data = "DD/MM/YYYY" if lang["lang_code"] == "pt" else "MM/DD/YYYY"

                with col_inicio:

                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>{lang['initial_date']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.session_state["dados_inicio"] = st.date_input(" ", value=dados_inicio, format=formato_data, label_visibility='collapsed')

                with col_fim:

                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>{lang['final_date']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.session_state["dados_fim"] = st.date_input(" ", value=dados_fim, format=formato_data, label_visibility='collapsed')

                with st.expander(f"{lang['quick_select']}", expanded=True):
                    col_inteiro, col_sete = st.columns(2, gap="small")

                    with col_inteiro:
                        if st.button(f"{lang['full_period']}", use_container_width=True):
                            st.session_state["dados_inicio"] = dados_inicio
                            st.session_state["dados_fim"] = dados_fim
                            st.session_state["ultimo_periodo"] = "inteiro"

                            from main_estrela_config import ESTACOES_ESTRELA
                    
                            if estacoes_info == ESTACOES_ESTRELA:
                                try:
                                    df_est6 = carregar_dados(ESTACOES_ESTRELA["EST6"]["url"])
                                    df_est6["datetime_ajustado"] = df_est6["datetime_utc"].dt.tz_convert(st.session_state["fuso_selecionado"])
                                    inicio_est6 = df_est6["datetime_ajustado"].min().date()

                                    # Só ajusta se estiver iniciando com o período total (primeira execução)
                                    if dados_inicio < inicio_est6:
                                        dados_inicio = inicio_est6

                                except Exception as e:
                                    st.warning(f"Não foi possível ajustar a data inicial com base na EST6: {e}")

                    with col_sete:
                        if st.button(f"{lang['last_7_days']}", use_container_width=True):
                            st.session_state["dados_inicio"] = (dados['datetime_ajustado'].max() - timedelta(days=7)).date()
                            st.session_state["dados_fim"] = dados['datetime_ajustado'].max().date()
                            st.session_state["ultimo_periodo"] = "7d"

                    _, col_24h, _ = st.columns([0.5, 1, 0.5], gap="small")

                    with col_24h:
                        if st.button(f"{lang['last_24_hours']}", use_container_width=True):
                            st.session_state["dados_inicio"] = (dados['datetime_ajustado'].max() - timedelta(hours=24)).date()
                            st.session_state["dados_fim"] = dados['datetime_ajustado'].max().date()
                            st.session_state["ultimo_periodo"] = "24h"

                st.markdown("<br>", unsafe_allow_html=True)            

        with col_grafico:

            with st.container(border=True):

                aba_grafico, aba_info, aba_mapa, aba_estatisticas = st.tabs(["Gráfico", "Info", "Mapa", "Estatísticas"])

                # ============================ GRÁFICO ============================
                with aba_grafico:

                    # Se for o app de Estrela e o cliente desejar sobreposição
                    usar_sobreposicao = False

                    from main_estrela_config import ESTACOES_ESTRELA

                    if estacoes_info == ESTACOES_ESTRELA:
                        usar_sobreposicao = st.toggle("Comparar estações", value=False)

                    if usar_sobreposicao:
                        plotar_sobreposicao_estrela(estacoes_info, lang)

                    else:    

                        dados_filtrados = filtrar_dados(st.session_state["dados_estacao"], 
                                                        st.session_state["dados_inicio"],
                                                        st.session_state["dados_fim"], st.session_state["fuso_selecionado"])
                        
                        # Aplica o corte de 1h apenas para fins gráficos
                        dados_filtrados = corte_ultima_1h(dados_filtrados)

                        cota_alerta, cota_inundacao = cotas_notaveis(estacao_selecionada, estacoes_info)

                        plotar_grafico(url_estacao, estacoes_info, dados_filtrados, estacao_selecionada, cota_alerta, cota_inundacao, 
                                    st.session_state["dados_inicio"], st.session_state["dados_fim"], lang)
                    
                # ============================ INFO ============================
                with aba_info:
                    estacao = estacoes_info.get(estacao_selecionada, {})
                    
                    descricao = estacao.get("descricao", "")
                    localizacao = estacao.get("localizacao", "Indisponível")
                    endereco = estacao.get("endereco", "Indisponível")
                    coord = estacao.get("coord", ["", ""])
                    altimetrica = estacao.get("altimetrica", "Indisponível")
                    altura_antena = estacao.get("altura_antena", "Indisponível")
                    inicio_operacao = estacao.get("inicio_operacao", "Indisponível")
                    status_estacao = verificar_status_estacao(dados["datetime_utc"].max())
                    cor_status = "green" if status_estacao == "Ativa" else "red"

                    col_img, col_dados = st.columns([1.2, 2], gap="large")

                    with col_img:

                        # Moldura para a foto da estação
                        with st.container(border=True):

                            exibir_imagem_estacao(estacoes_info.get(estacao_selecionada))

                            

                    with col_dados:

                        st.markdown(f"""
                            <h4 style='margin-bottom: 0.5rem;'>Estação {estacao_selecionada}</h4>
                            <p><strong>Localização:</strong> {localizacao}</p>
                            <p><strong>Endereço:</strong> {endereco}</p>
                            <p><strong>Coordenadas:</strong> {coord[0]}, {coord[1]}</p>
                            <p><strong>Referência altimétrica:</strong> {altimetrica}</p>
                            <p><strong>Altura da antena em relação à água:</strong> {altura_antena} m</p>
                            <p><strong>Início de operação:</strong> {inicio_operacao}</p>
                            <p><strong>Situação:</strong> <span style='color:{cor_status}; font-weight:bold'>{status_estacao}</span></p>
                        """, unsafe_allow_html=True)


                # ============================ MAPA ============================
                with aba_mapa:

                    exibir_mapa_estacao(estacoes_info.get(estacao_selecionada))

                # ============================ ESTATÍSTICAS ============================
                with aba_estatisticas:
                        
                    df_estat = st.session_state["dados_estacao"][["datetime_ajustado", "water_level(m)"]].copy()
                    df_estat = df_estat.sort_values("datetime_ajustado", ascending=False)
                    df_estat.rename(columns={
                        "datetime_ajustado": "Hora" if lang["lang_code"] == "pt" else "Time",
                        "water_level(m)": "Nível (m)" if lang["lang_code"] == "pt" else "Level (m)"
                    }, inplace=True)

                    st.markdown("#### Nível das últimas 12h" if lang["lang_code"] == "pt" else "#### Last 12h Water Levels")
                    st.dataframe(df_estat.head(12), use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Seção com Situação do nível | Nível recente + atualização | Velocidade (em breve)
            col_situacao, col_nivel, col_velocidade = st.columns([1.2, 1.8, 1.2])

            # 🔹 Situação do nível
            cota_alerta, cota_inundacao = cotas_notaveis(estacao_selecionada, estacoes_info)

            df_nivel = carregar_dados(url_estacao)

            nivel_formatado, dh_ultima_formatada = nivel_recente(df_nivel, st.session_state["fuso_selecionado"], lang, modo="ajustado")

            velocidade_formatada = calcular_velocidade(df_nivel)

            nivel_valor = float(nivel_formatado.replace(",", ".").replace("&nbsp;m", ""))

            situacao, cor_situacao = situacao_nivel(nivel_valor, cota_alerta, cota_inundacao)

            rotulo_situacao = {
                    "Normal": {"pt": "Normal", "en": "Normal level"},
                    "Alerta": {"pt": "Em alerta", "en": "Alert"},
                    "Inundação": {"pt": "Inundação", "en": "Flood"},
                    "Indisponível": {"pt": "Indisponível", "en": "Unavailable"}
                }
            mensagem_situacao = rotulo_situacao[situacao][lang["lang_code"]]

            with col_situacao:
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 22px; margin: 0;'>
                                Situação do nível:
                                <span style='font-weight: bold; color: {cor_situacao};'>{mensagem_situacao}</p>
                        </div>
                    """, unsafe_allow_html=True)

            # 🔹 Nível recente
            with col_nivel:

                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 22px; margin: 0;'>
                                {lang['recent_level']}:
                                <span style='font-weight: bold; color: {cor_texto};'>{nivel_formatado}</span>
                            </p>
                            <p style='font-size: 13px; margin: 0;'>{lang['update'] + ':'} {dh_ultima_formatada}</p>
                        </div>
                    """, unsafe_allow_html=True)

            # 🔹 Velocidade futura (placeholder)
            with col_velocidade:
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 22px; margin: 0;'>
                                Velocidade:
                                <span style='font-weight: bold; color: {cor_texto};'>{velocidade_formatada}</span>
                            </p>
                        </div>
                    """, unsafe_allow_html=True)    

    _, col_modo, col_fuso, _ = st.columns([0.5, 1, 1.3, 0.5], gap="small", vertical_alignment="top")

    
    with st.container():

        with col_modo:

            modo_visualizacao(lang)

        with col_fuso:

            fuso_horario(lang)



    _, col_img_estac, _, col_mapa, _ = st.columns([0.1, 2, 0.5, 4, 0.9])

    with col_img_estac:

        # Moldura para a foto da estação
        with st.container(border=True):

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
        with st.container(border=True, height=400):

            # Obtém os dados da estação selecionada
            estacao = estacoes_info.get(estacao_nome)

            _, _, cor_mapa, cor_localizacao, _ = obter_tema()

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
                
                st.pydeck_chart(deck, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)