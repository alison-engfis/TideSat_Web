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
import plotly.graph_objects as go
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
def checar_senha():
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
            st.error("😕 Senha incorreta. Tente novamente")

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

    # CSS para personalizar e evitar a quebra de linhas nos botões (PROVAVELMENTE SERÁ EXTINTO DO PROJETO MUITO EM BREVE)
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

    # Ocultando menu e rodapé (via CSS)
    esconder = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stActionButton {display: none;}
        </style>
        """
    st.markdown(esconder, unsafe_allow_html=True)

# Função para carregar os dados das estações (via URL individual)
def carregar_dados(url):
    resposta = requests.get(url, verify=False, timeout=100)

    if resposta.status_code != 200:
        st.warning("Erro ao acessar os dados da estação selecionada.")
        st.stop()

    dados_nivel = StringIO(resposta.text)
    df = pd.read_csv(dados_nivel, sep=',')

    if df.empty:
        st.warning("Erro ao carregar os dados da estação selecionada.")
        st.stop()

    df.rename(columns={
        '% year': 'year', ' month': 'month', ' day': 'day',
        ' hour': 'hour', ' minute': 'minute', ' second (GMT/UTC)': 'second',
        ' water level (meters)': 'water_level(m)'}, inplace=True)

    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
    df['datetime_utc'] = df['datetime'].dt.tz_localize('UTC')

    # Adicionando a coluna `datetime_ajustado`
    fuso_selecionado = st.session_state.get("fuso_selecionado", "America/Sao_Paulo")
    df['datetime_ajustado'] = df['datetime_utc'].dt.tz_convert(fuso_selecionado)

    return df

# Função do seletor de fuso
def fuso_horario():

    # Lista de todos os fusos horários disponíveis
    fusos = pytz.all_timezones

    # Verifica se há um fuso horário armazenado no session_state
    if "fuso_selecionado" not in st.session_state:
        st.session_state["fuso_selecionado"] = TIMEZONE_PADRAO  # Define o fuso padrão apenas na inicialização

    fuso_atual = st.session_state["fuso_selecionado"]

    _, col_fuso, _ = st.columns([0.3, 1, 0.3])

    with col_fuso:

        # Usando expander para esconder ou mostrar o seletor com fuso atual
        with st.expander(f"🕓 Fuso horário: {fuso_atual}", expanded=False):
            
            # Seletor de fuso horário dentro do expander
            fuso_selecionado = st.selectbox(
                " ", 
                fusos, 
                index=fusos.index(fuso_atual),  # Mantém o índice correto
                label_visibility='collapsed', 
                key="fuso_selecionado"  # Vincula ao session_state
            )

    return fuso_selecionado

# Função para formatar o nível recente via mediana (ADICIONADA A LÓGICA PARA A VELOCIDADE)
def velocidade_nivel_recente(df, fuso_selecionado):

    # Define o limite de tempo para as últimas 6 horas
    limite_tempo = df["datetime_utc"].max() - timedelta(hours=6)
    ultimas_6h = df[df["datetime_utc"] >= limite_tempo]

    if ultimas_6h.empty:
        st.stop()

    # Cria coluna com tempo em horas (relativo ao primeiro ponto)
    t0 = ultimas_6h["datetime_utc"].min()
    ultimas_6h = ultimas_6h.copy()
    ultimas_6h["tempo_h"] = (ultimas_6h["datetime_utc"] - t0).dt.total_seconds() / 3600.0

    # Ajuste de reta (polinômio de grau 1)
    coef = np.polyfit(ultimas_6h["tempo_h"], ultimas_6h["water_level(m)"], 1)

    inclinacao = coef[0]  # m/h
    nivel_recente = coef[1]  # Nível estimado no início

    # Formatando para se adequar as necessidades do layout
    nivel_formatado = f"{nivel_recente:.2f}&nbsp;m".replace('.', ',')
    inclinacao_formatada = f"{inclinacao:.2f}&nbsp;m/h".replace('.', ',')
    dh_ultima_formatada = df["datetime_utc"].max().tz_convert(fuso_selecionado).strftime('%d/%m/%Y - %H:%M')

    return inclinacao_formatada, nivel_formatado, dh_ultima_formatada

# Função para exibir as cotas notáveis nos filtros
def cotas_notaveis(estacao_nome, estacoes_info):

    # Recupera as cotas notáveis para a estação selecionada
    cotas = estacoes_info.get(estacao_nome, {})
    cota_alerta = cotas.get("cota_alerta")
    cota_inundacao = cotas.get("cota_inundacao")

    return cota_alerta, cota_inundacao

# Função para converter a imagem para base64
def converter_base64(caminho_imagem):

    try:
        
        with open(caminho_imagem, "rb") as file:
            link = base64.b64encode(file.read()).decode()

        return link
        
    except Exception as e:

        print(f"Erro ao converter imagem: {e}")

        return None

# Função que configura a exibição do gráfico
def plotar_grafico(url, estacao_selecionada, cota_alerta, cota_inundacao, dados_inicio, dados_fim):
    cor_linha, _, _, _, _ = obter_tema()

    # 🔹 Carrega todos os dados da estação
    df_completo = carregar_dados(url)

    if df_completo is None or df_completo.empty:
        st.write(f"Nenhum dado encontrado para a estação {estacao_selecionada}.")
        st.stop()

    # 🔹 Prepara zoom inicial com base nos inputs do usuário
    fuso = st.session_state["fuso_selecionado"]
    zoom_inicio = pd.to_datetime(dados_inicio).tz_localize(fuso)
    zoom_fim = pd.to_datetime(dados_fim).tz_localize(fuso)

    # 🔹 Criação do gráfico com todos os dados visíveis
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_completo['datetime_ajustado'],
        y=df_completo['water_level(m)'],
        line=dict(color=cor_linha),
        showlegend=False,
        hovertemplate='Data: %{x|%d/%m/%Y %H:%M}<br>Nível (m): %{y:.2f}<extra></extra>',
    ))

    # Cotas de inundação e alerta
    if cota_inundacao is not None:
        fig.add_shape(
            type="line", xref="paper", yref="y",
            x0=0, x1=1, y0=cota_inundacao, y1=cota_inundacao,
            line=dict(color="#FF0000", dash="dash"),
            name="Cota de inundação", legendgroup="cota_inundacao", showlegend=True
        )

    if cota_alerta is not None:
        fig.add_shape(
            type="line", xref="paper", yref="y",
            x0=0, x1=1, y0=cota_alerta, y1=cota_alerta,
            line=dict(color="#FFA500", dash="dash"),
            name="Cota de alerta", legendgroup="cota_alerta", showlegend=True
        )

    # Layout interativo com zoom inicial e navegação total
    fig.update_layout(
            xaxis=dict(
            title="Data",
            titlefont=dict(size=16),
            range=[zoom_inicio, zoom_fim],
            rangeslider=dict(visible=False),
            type="date"
        ),
        yaxis=dict(
            title="Nível medido (m)",
            titlefont=dict(size=16)
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1,
            xanchor='center',
            x=0.7
        ),
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
        autosize=True
    )

    st.plotly_chart(fig, use_container_width=True)

# Função para obter as configurações do tema
def obter_tema():
    
    ms = st.session_state

    # Obtém o tema do config.toml
    tema_padrao = "escuro" if st.get_option("theme.base") == "dark" else "claro"

    if "temas" not in ms:
        ms.temas = {
            "tema_atual": tema_padrao,
            "atualizado": True,
            "claro": {
                "theme.base": "light",
                #"theme.backgroundColor": "#121212",
                "theme.primaryColor": "#0065cc",
                "theme.secondaryBackgroundColor": "#e1e4e8",
                "theme.textColor": "#0a1464",
                "icone_botoes": "Claro",
                "cor_linha": "#0065cc",
                "cor_texto": "#0061c3",
                "cor_mapa": "#0065cc"
            },
            "escuro": {
                "theme.base": "dark",
                #"theme.backgroundColor": "#ffffff",
                "theme.primaryColor": "#87CEEB",
                "theme.secondaryBackgroundColor": "#262B36",
                "theme.textColor": "white",
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
def modo_visualizacao():
    _, _, _, _, ms = obter_tema()

    # Determina o ícone do botão baseado no tema atual
    icone_botoes = (
        ms.temas["claro"]["icone_botoes"]
        if ms.temas["tema_atual"] == "claro"
        else ms.temas["escuro"]["icone_botoes"]
    )

    _, col_visual, _ = st.columns([0.5, 1, 0.5])

    with col_visual:

        # Usando um expander para o seletor de modo de visualização
        with st.expander(f"👓 Tema: {icone_botoes}", expanded=False):

            # Botão para alternar o tema
            st.button(icone_botoes, on_click=MudarTema)

# Função para construir o layout
def main(estacoes_info, estacao_padrao): 

    configurar_layout()

    tz_padrao = TIMEZONE_PADRAO

    if "fuso_selecionado" not in st.session_state:
        st.session_state["fuso_selecionado"] = tz_padrao

    with st.container(border=True):

        # Colunas principais
        _, col_filtros, _, col_grafico, _ = st.columns([0.1, 1.1, 0.1, 3, 0.1], gap="small", vertical_alignment="top")

        _, cor_texto, _, _, _ = obter_tema()

        with col_filtros:

            with st.container():

                col_img = st.columns([1])[0]

                with col_img:

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

                col_estacao = st.columns([1])[0]

                with col_estacao:

                    st.markdown("""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>Estação de medição</p>
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

                col_inicio, col_fim = st.columns(2, gap="small")

                with col_inicio:

                    st.markdown("""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>Data inicial</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.session_state["dados_inicio"] = st.date_input(" ", value=dados_inicio, format="DD/MM/YYYY", label_visibility='collapsed')

                with col_fim:

                    st.markdown("""
                        <div style='text-align: center;'>
                            <p style='font-size: 14px; margin: 0;'>Data final</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.session_state["dados_fim"] = st.date_input(" ", value=dados_fim, format="DD/MM/YYYY", label_visibility='collapsed')
                
                with st.expander(f"📅 Seleção rápida de período", expanded=True):
                    col_inteiro, col_sete = st.columns(2, gap="small")

                    with col_inteiro:
                        if st.button('Período inteiro', use_container_width=True):
                            st.session_state["dados_inicio"] = dados_inicio
                            st.session_state["dados_fim"] = dados_fim

                    with col_sete:
                        if st.button('Últimos 7 dias', use_container_width=True):
                            st.session_state["dados_inicio"] = (dados['datetime_ajustado'].max() - timedelta(days=7)).date()
                            st.session_state["dados_fim"] = dados['datetime_ajustado'].max().date()

                    _, col_24h, _ = st.columns([0.7, 1, 0.7], gap="small")

                    with col_24h:
                        if st.button('Últimas 24h', use_container_width=True):
                            st.session_state["dados_inicio"] = (dados['datetime_ajustado'].max() - timedelta(hours=24)).date()
                            st.session_state["dados_fim"] = dados['datetime_ajustado'].max().date()

                col_recente = st.columns([1])[0]

                with col_recente:

                    df_nivel = carregar_dados(url_estacao) 
                    velocidade, nivel, dh_ultima_formatada = velocidade_nivel_recente(df_nivel, st.session_state["fuso_selecionado"])

                    if velocidade is not None and nivel is not None:

                        # velocidade_numerica = float(velocidade.replace("&nbsp;m/h", "").replace(",", "."))

                        # cor_velocidade = "green" if velocidade_numerica > 0 else "orange"

                        st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 17px; margin: 0;'>Nível recente: 
                            <span style='color:{cor_texto};'>{nivel}</span></p>
                        
                        </div>
                        """, unsafe_allow_html=True)
                                        
                    # st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown(f"""<div style='text-align: center;'>
                            <p style='font-size: 13px; margin: 0;'>Atualização: {dh_ultima_formatada}</p>
                            </div>""", unsafe_allow_html=True)

        with col_grafico:

            with st.container():
                
                cota_alerta, cota_inundacao = cotas_notaveis(estacao_selecionada, estacoes_info)

                plotar_grafico(url_estacao, estacao_selecionada, cota_alerta, cota_inundacao, st.session_state["dados_inicio"], st.session_state["dados_fim"])

    _, col_modo, col_fuso, _ = st.columns([0.5, 1, 1.3, 0.5], gap="small", vertical_alignment="top")

    
    with st.container():

        with col_modo:

            modo_visualizacao()

        with col_fuso:

            fuso_horario()

# No início da execução, restauramos a estação selecionada
def restaurar_estacao_e_periodo():
    if "estacao_selecionada" in st.session_state:
        estacao_selecionada = st.session_state["estacao_selecionada"]

    if "ultimo_periodo" in st.session_state:
        ultimo_periodo = st.session_state["ultimo_periodo"]

    # Garante que o período anterior seja restaurado corretamente
    if "ultimo_periodo_temp" in st.session_state:
        st.session_state["ultimo_periodo"] = st.session_state.pop("ultimo_periodo_temp")         
        
# [TEMPORARIAMENTE DESATIVADA (QUIÇÁ PARA SEMPRE)] Função para filtrar os dados pelo período selecionado
def filtrar_dados(df, dados_inicio, dados_fim, fuso_selecionado):

    # Convertendo dados_inicio e dados_fim para datetime no fuso selecionado
    dados_inicio_dt = pd.to_datetime(dados_inicio).tz_localize(fuso_selecionado)
    dados_fim_dt = pd.to_datetime(dados_fim).tz_localize(fuso_selecionado)

    # Obtendo o intervalo completo dos dados
    dados_inicio_total = df['datetime_ajustado'].min()
    dados_fim_total = df['datetime_ajustado'].max()

    # Verifica se o período solicitado é o mesmo que o intervalo completo
    if dados_inicio_dt == dados_inicio_total and dados_fim_dt == dados_fim_total:
        
        # Retorna o DataFrame original sem filtrar
        return df

    # Aplica o filtro nos dados
    filtro = (df['datetime_ajustado'] >= dados_inicio_dt) & (df['datetime_ajustado'] < dados_fim_dt + timedelta(days=1))

    return df.loc[filtro]

# (TEMPORÁRIAMENTE DESATIVADA) Função para configurar a imagem e o mapa da estação selecionada
def imagem_mapa_estacao(estacao_nome, estacoes_info):

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