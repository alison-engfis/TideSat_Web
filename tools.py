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
import extra_streamlit_components as stx

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

# Função para formatar o nível recente via mediana
def nivel_recente(df, fuso_selecionado, lang):

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

    if lang["lang_code"] == "en":

        dh_ultima_formatada = dh_ultima.strftime('%m/%d/%Y - %I:%M %p')

    else:
        dh_ultima_formatada = dh_ultima.strftime('%d/%m/%Y - %H:%M')

    return nivel_formatado, dh_ultima_formatada

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
        labels={'datetime_ajustado': "Data" if lang["lang_code"] == "pt" else "Date", 'water_level(m)': "Nível (m)" if lang["lang_code"] == "pt" else "Level (m)"}
    )
    # Configurações dos eixos
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=True)

    # Condição para aplicar o ajuste no eixo Y apenas se o período for "{lang['last_24_hours']}"
    if (dados_fim - dados_inicio) == pd.Timedelta(hours=24):
        
        med = np.median(dados_filtrados['water_level(m)'])
        tempmin = med - 0.5
        tempmax = med + 0.5
        fig.update_yaxes(autorangeoptions_clipmin=tempmin, autorangeoptions_clipmax=tempmax, fixedrange=True)

    elif (dados_fim - dados_inicio) >= pd.Timedelta(days=7):  # Inclui Período Inteiro e {lang['last_7_days']}

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

                    if pd.isna(dados_inicio) or pd.isna(dados_fim):
                        st.warning("A estação selecionada ainda não possui dados suficientes para exibição.")
                        st.stop()


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
                          
                          # Passando 'ultimo_periodo' para MudarTema para garantir que ele seja mantido
                    if 'ultimo_periodo' in st.session_state:
                        ultimo_periodo_temp = st.session_state['ultimo_periodo']

                col_recente = st.columns([1])[0]

                with col_recente:

                    df_nivel = carregar_dados(url_estacao)
                    
                    nivel_formatado, dh_ultima_formatada = nivel_recente(df_nivel, st.session_state["fuso_selecionado"], lang)
                    
                    st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <p style='font-size: 17px; margin: 0;'>{lang['recent_level'] + ':'} <span style='color:{cor_texto};'>{nivel_formatado}</span></p>
                        <div style='text-align: center;'>
                            <p style='font-size: 13px; margin: 0;'>{lang['update'] + ':'} {dh_ultima_formatada}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)

        with col_grafico:
            with st.container():

                dados_filtrados = filtrar_dados(st.session_state["dados_estacao"], st.session_state["dados_inicio"],
                    st.session_state["dados_fim"], st.session_state["fuso_selecionado"])
                cota_alerta, cota_inundacao = cotas_notaveis(estacao_selecionada, estacoes_info)

                plotar_grafico(url_estacao, estacoes_info, dados_filtrados, estacao_selecionada, cota_alerta, cota_inundacao, 
                               st.session_state["dados_inicio"], st.session_state["dados_fim"], lang)

    _, col_modo, col_fuso, _ = st.columns([0.5, 1, 1.3, 0.5], gap="small", vertical_alignment="top")

    
    with st.container():

        with col_modo:

            modo_visualizacao(lang)

        with col_fuso:

            fuso_horario(lang)

# No início da execução, restauramos a estação selecionada
def restaurar_estacao_e_periodo():
    if "estacao_selecionada" in st.session_state:
        estacao_selecionada = st.session_state["estacao_selecionada"]

    if "ultimo_periodo" in st.session_state:
        ultimo_periodo = st.session_state["ultimo_periodo"]

    # 🔹 Garante que o período anterior seja restaurado corretamente
    if "ultimo_periodo_temp" in st.session_state:
        st.session_state["ultimo_periodo"] = st.session_state.pop("ultimo_periodo_temp")         
        
restaurar_estacao_e_periodo()

# [TEMPORÁRIAMENTE DESATIVADA (QUIÇÁ PARA SEMPRE)] Função para filtrar os dados pelo período selecionado
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