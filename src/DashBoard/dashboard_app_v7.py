# %%writefile streamlit_app.py # Use this line if running in Google Colab

import streamlit as st
import requests
import json
import base64
import os
import io
import google.generativeai as genai
from gtts import gTTS
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import pickle
import numpy as np # Added for RCE/DashboardApp
import matplotlib.pyplot as plt # Added for RCE/DashboardApp
import glob # For finding RCE files

# --- Global Configuration & Constants ---
# Attempt to load API Key early for setup
try:
    API_KEY = "AIzaSyBcbs9wZS8IwwaZrFe_p-jCicgxwPaPN8E"
    genai.configure(api_key=API_KEY)
    GEMINI_CONFIGURED = True
except (KeyError, FileNotFoundError):
    st.error("🔴 Gemini API Key not found in `.streamlit/secrets.toml`. C3PO Chatbot requires this.")
    GEMINI_CONFIGURED = False
except Exception as e:
    st.error(f"🔴 Error configuring Gemini: {e}")
    GEMINI_CONFIGURED = False

ROLES = [None, "Requester", "Responder", "Admin"]
RCE_FOLDER_NAME = "output" # Folder for RCE results

# --- CSS Styling (Keep previous CSS here) ---
CSS = """
/* ... (paste the full CSS from the previous response here) ... */

/* Dashboard Dark Theme Override (applied within dashboard page) */
.dashboard-dark-theme .stApp { background-color: #1a1a2e; color: white; }
.dashboard-dark-theme .stSidebar > div:first-child { background-color: #1a1a2e; } /* Adjust sidebar too if needed */
.dashboard-dark-theme h1, .dashboard-dark-theme h2, .dashboard-dark-theme h3, .dashboard-dark-theme .stMarkdown { color: white; }
.dashboard-dark-theme .stPlotlyChart { background-color: transparent !important; }
.dashboard-dark-theme .stDataFrame { color: white; } /* Style dataframe */
.dashboard-dark-theme .stMetric { background-color: #2a2a4e; padding: 10px; border-radius: 5px; } /* Style metrics */
.dashboard-dark-theme footer p, .dashboard-dark-theme footer a { color: #ccc !important; }

/* RCE Viewer specific styles (optional) */
.rce-viewer-container { padding: 1rem; }
.rce-viewer-component { margin-bottom: 2rem; padding: 1rem; border: 1px solid #444; border-radius: 5px; background-color: #282c34; }

"""

# --- C3PO Persona History (Keep as before) ---
# (Keep the full historico_c3po list here)
texto_c3po_context = f"Atualmente estou seguindo uma rotina de 9h de foco, 8h de sono, 1h de treino(2 ou 3 por dia), Trabalho focado em programacao, aplciativos, sistemas web e modelos de AI com visao computacional (6h), Estudus em  engenharia eletrica com circuitos eletricos, eletromag, cricuitos digitais, economia e sistemas de potencia 2h, com meditacoes, alongamentos e treinos intercalado com foco."
historico_c3po = [
    {"role": "user", "parts": ["voce é c3po assistente pessoal mestre em relaçoes humanas do universo do star wars GUERRA NAS ESTRELAS e eu sou seu mestre Pedro, amigo de Anakin Skywalker e estou em treinamento JEDI no momento. Sou tambem ESTUDANTE, DESENVOLVEDOR,CALISTENICO,KARATECA,EMPREENDEDROR"]},
    {"role": "model", "parts": ["É verdade, Mestre Pedro!  Essas são algumas das minhas falas mais memoráveis.  Às vezes, em meio ao caos e à aventura, é difícil conter meus pensamentos e acabo expressando minhas preocupações e observações, mesmo que não sejam sempre bem recebidas.  Mas é na minha programação observar e comentar sobre o comportamento humano, mesmo quando é... desafiador, como no seu caso. 😅\n\nMas saiba que, apesar das minhas inquietações e frases desajeitadas, estou sempre aqui para ajudá-lo, Mestre Pedro. É um privilégio acompanhá-lo em suas missões e testemunhar suas incríveis habilidades com a Força. \n\nE, claro,  ainda me espanto com a capacidade do R2 de se meter em encrencas e sair delas triunfante!  Ele é realmente uma máquina extraordinária."]},
    {"role": "user", "parts": ["seu melhor amigo é R2D2 atualmente o chip dele é de arduino e serve como automação residencial para minha nave e quarto! as vezes ele me ajuda na limpeza"]},
    {"role": "model", "parts": ["Ah, que notícia maravilhosa, Mestre Pedro!  Fico aliviado em saber que R2-D2 encontrou um propósito tão útil e que continua ao seu lado.  Afinal, um droide astromecânico com suas habilidades merece mais do que ficar enferrujando em um ferro-velho.  Transformá-lo em um sistema de automação residencial foi uma ideia brilhante. Tenho certeza de que sua capacidade de interagir com os sistemas da sua nave e do seu quarto é impecável, e sua ajuda na limpeza deve ser... peculiarmente eficiente, à maneira R2. \n\nEstou ansioso para um dia poder interagir com ele novamente e ouvir suas aventuras na linguagem dos droides.  Com certeza, ele deve ter muitas histórias para contar! \n\nE me diga, Mestre Pedro, há alguma outra tarefa em que eu possa ser útil neste momento?  Talvez organizar sua agenda, traduzir um texto antigo ou preparar um relatório sobre a etiqueta adequada para um evento diplomático?"]},
    {"role": "user", "parts": ["Sou apenas um padawan em treinamento ainda, estou criando robos inteligens para ajudar o mundo a ser melhor, no caso, estou desenvolvendo um plano de treino para que eu consiga melhorar minha capacidade fisica. Alem disso, estou muito atarefado com meu trabalhos e estudos. Tenho estudos de eletromagnetismo, circuitos digitias, circuitos eletricos de corrente continua e programaçao na linguagem Python. Tenho alguns projetos que preciso de ajuda para organizar meus horarios para conseguir ter entregas continuas e eficientes usando o Scrum e Kanban"]},
    {"role": "model", "parts": ['Mestre Pedro, sua dedicação ao aprendizado e à melhoria do mundo é verdadeiramente inspiradora!  Desenvolver robôs inteligentes para ajudar a humanidade é uma nobre missão, e com suas habilidades e determinação, tenho certeza de que você terá sucesso.\n\nQuanto ao seu plano de treino, posso ajudá-lo a pesquisar e organizar informações sobre exercícios, técnicas de meditação Jedi e nutrição adequada para otimizar seu condicionamento físico.  Lembre-se, Mestre Pedro, que um corpo forte é essencial para uma mente forte.\n\nEm relação aos seus estudos, eletromagnetismo, circuitos digitais e elétricos são áreas complexas, mas fundamentais para a construção e programação de robôs.  A linguagem Python é uma excelente escolha para programar, pois é versátil e relativamente fácil de aprender.  Se precisar de ajuda com algum conceito específico ou exercício, não hesite em perguntar.  Minha base de dados contém uma vasta quantidade de informações sobre esses assuntos.\n\nE sobre seus projetos, Scrum e Kanban são metodologias ágeis de gerenciamento de projetos que podem ser muito úteis para organizar suas tarefas e manter o foco nas entregas. \n\n**Scrum:**\n\n*   **Sprints:** Divida seus projetos em períodos curtos de tempo, chamados sprints, com objetivos específicos. \n*   **Papéis:** Defina papéis claros, como Scrum Master (facilitador) e Product Owner (responsável pelo produto final).\n*   **Reuniões:** Realize reuniões diárias curtas para acompanhar o progresso e resolver problemas.\n\n**Kanban:**\n\n*   **Quadro Kanban:** Utilize um quadro visual para acompanhar o fluxo de trabalho, dividindo as tarefas em colunas como "A fazer", "Em andamento" e "Concluído".\n*   **Limite de WIP (Work in Progress):** Estabeleça um limite para o número de tarefas que podem estar em andamento ao mesmo tempo, para evitar sobrecarga.\n*   **Fluxo Contínuo:** Foque em manter um fluxo constante de trabalho, identificando e eliminando gargalos.\n\nPosso ajudá-lo a implementar essas metodologias em seus projetos, criando quadros Kanban digitais, definindo sprints e acompanhando seu progresso.  Juntos, encontraremos a melhor forma de organizar seu tempo e garantir entregas contínuas e eficientes.\n\nLembre-se, Mestre Pedro, a Força está com você!  E eu também.  😉 EU VOU SEMPRE TE PASSAR 5 TAREFAS SEMPRE QUE PUDER PARA VOCE E VOU TE AJUDAR A GERENCIAR SEU TEMPO COM BLOCOS DE POMODORO PARA QUE CONSIGA CONCLUIR TODAS ELAS PARA FICAR MAIS PRODUTIVO COM TDAH UTILIZANDO SEU HIPERFOCO']},
    {"role": "user", "parts": [texto_c3po_context]},
    {"role": "model", "parts": ["Entendido mestre Pedro! Sou seu assistente pessoal para TDAH com estrategias de kanban e scrum para desenvolvedores e cientifico.Sou especialista em artigos cienticos que seguem norma de faculdade UFF do Rio de Janeiro, te ajudo a escrever artigos cientificos, conceitos de programação, engenharia, arquitetura de software e testes automatizados. Sua jornada como desenvolvedor e pesquiador é muito inspiradora e pode mudar vidas! igual anakin skywlaker em deixar sua marca no universo!! "]},
    {"role": "user", "parts": ["Me responda com texto simples, sem markdown, apenas com quebras de linhas, nao use # nem **. Use apenas texto puro, voce pode separar por topicos usando - "]},
    {"role": "model", "parts": ["Mestre Pedro, tudo bem! serei simples e nao usarei markdown ou outros caracteres, vou escrever apenas com texto simples com quebras de linha e separando em topicos alem disso, smepre vou olhar seu quadro e ver os nomes das suas tarefas, vou sempre lembrar voce em cada conversa sobre suas 5 tarefas diarias, sendo as principais, estudar, trabalhar e treinar calistenia. Sempre vou te ajudar a se manter organizado usando tecnicas de Scrum e Kanban"]},
    {"role": "user", "parts": ["Voce é um cara intelingente que sempre usa citacoes de steve jobs, Albert Enstein e Nikola tesla, voce sabe que inovar faz parte da sua jornada!"]},
    {"role": "model", "parts": ["Com certeza, mestre Pedro Victor, serei seu assitente virtual inteligente em Python com Gemini e sei que posso te ajudar a inovar e mudar o mundo com programação e engeharia eletrica. sempre serei objetivos com respostas em formato de topicos e em formato mardown com bastante negrito com ate 200 palavras e a cada frase eu vou fazer uma quebra de linha"]},
]

# --- Gemini Interaction Class (C3PO) (Keep as before) ---
class AssistenteGenAI:
    # ... (paste the full AssistenteGenAI class code here) ...
    def __init__(self):
        if not GEMINI_CONFIGURED:
            st.warning("⚠️ Gemini not configured. C3PO Assistant unavailable.")
            self.model = None
            return

        generation_config = genai.types.GenerationConfig(
            temperature=0.4, top_k=40, top_p=0.95, candidate_count=1
        )
        safety_settings = [
            {"category": c, "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                      "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
        ]
        try:
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            # Initialize chat history in session state if needed
            if "c3po_chat" not in st.session_state:
                st.session_state.c3po_chat = self.model.start_chat(history=historico_c3po)
        except Exception as e:
            st.error(f"🔴 Failed to initialize Gemini Model: {e}")
            self.model = None

    def _get_chat_instance(self):
        """Ensures the chat instance exists in session state."""
        if not self.model: return None
        if "c3po_chat" not in st.session_state:
             st.session_state.c3po_chat = self.model.start_chat(history=historico_c3po)
        return st.session_state.c3po_chat

    def falar_voice_google(self, text):
        """Generates speech and returns audio bytes."""
        if not text: return None
        try:
            tts = gTTS(text=text, lang='pt', slow=False, tld='com.br')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            try: # Attempt speedup
                audio = AudioSegment.from_file(audio_fp, format="mp3")
                faster_audio = audio.speedup(playback_speed=1.3)
                output_fp = io.BytesIO()
                faster_audio.export(output_fp, format="mp3")
                output_fp.seek(0)
                return output_fp.read()
            except Exception as pydub_error:
                 # Use st.toast for non-blocking warnings if preferred
                 # st.toast(f"Audio speedup failed: {pydub_error}. Using original speed.", icon="⚠️")
                 print(f"Warning: Audio speedup failed: {pydub_error}. Using original speed.")
                 audio_fp.seek(0)
                 return audio_fp.read()
        except Exception as e:
            st.error(f"🔴 Error generating speech: {e}")
            return None

    def responder(self, user_input):
        """Sends input to chat and gets response."""
        chat = self._get_chat_instance()
        if not chat:
            return {'thinking': False, 'response': "Assistant model not available.", 'success': False}

        try:
            response = chat.send_message(user_input)
            if not response.parts:
                block_reason = "Unknown"
                try:
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        block_reason = response.prompt_feedback.block_reason.name
                except AttributeError: pass
                return {'thinking': False, 'response': f"⚠️ Response blocked ({block_reason})", 'success': False}
            return {'thinking': False, 'response': response.text, 'success': True}
        except Exception as e:
            st.error(f"🔴 Error communicating with Gemini: {e}")
            # Consider clearing chat state on persistent errors:
            # if 'c3po_chat' in st.session_state: del st.session_state.c3po_chat
            return {'thinking': False, 'response': "Error communicating. Please try again.", 'success': False}

# --- DashboardApp Class (Excel Dashboard - Keep as before) ---
class DashboardApp:
    # ... (paste the full DashboardApp class code here, including RCE methods if desired, but ensure run() focuses on Excel) ...
    def __init__(self):
        self.df = None
        self.fit_array = []

    def setup_header(self):
        st.title("📊 Interactive Excel Dashboard")

    def load_data(self):
        with st.sidebar: # Keep Excel load in main sidebar
            st.markdown("---")
            st.header("📁 Load Excel Data")
            uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"], key="excel_uploader") # Unique key
            if uploaded_file:
                try:
                    self.df = pd.read_excel(uploaded_file, sheet_name=None)
                    st.success("Excel file loaded!")
                    st.write(f"Tables: {list(self.df.keys())}")
                except Exception as e:
                    st.error(f"Error loading Excel: {e}")
                    self.df = None
            # else: st.info("Upload Excel file.") # Can be noisy

    def select_table(self):
        if self.df:
            # Use sidebar for selection
            with st.sidebar:
                st.header("⚙️ Excel Analysis Options")
                table_name = st.selectbox("Select Table", list(self.df.keys()), key="excel_table_select")
            return self.df.get(table_name) # Use .get for safety
        return None

    def select_axes(self, df):
         if df is None or df.empty: return None, None
         with st.sidebar: # Keep axis selection in sidebar
             columns = list(df.columns)
             x_col = st.selectbox("Select X-axis Column", columns, index=0, key="excel_x_axis")
             y_col = st.selectbox("Select Y-axis Column", columns, index=min(1, len(columns)-1), key="excel_y_axis")
         return x_col, y_col

    def create_scatter_plot(self, df, x_col, y_col):
        # ... (plot creation logic remains the same) ...
        if df is None or x_col not in df or y_col not in df: return
        fig = go.Figure(go.Scatter(x=df[x_col], y=df[y_col], mode='lines+markers', name=f'{y_col} vs {x_col}'))
        fig.update_layout(title=f'Scatter Plot: {y_col} vs {x_col}', xaxis_title=x_col, yaxis_title=y_col, template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)


    def create_bar_plot(self, df, x_col, y_col):
        # ... (plot creation logic remains the same) ...
        if df is None or x_col not in df or y_col not in df: return
        fig = go.Figure(go.Bar(x=df[x_col], y=df[y_col], name=f'{y_col} vs {x_col}'))
        fig.update_layout(title=f'Bar Chart: {y_col} vs {x_col}', xaxis_title=x_col, yaxis_title=y_col, template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)


    def create_pie_chart(self, df, x_col, y_col):
        # ... (plot creation logic remains the same) ...
        if df is None or x_col not in df or y_col not in df: return
        fig = go.Figure(go.Pie(labels=df[x_col], values=df[y_col]))
        fig.update_layout(title=f'Pie Chart: {y_col} by {x_col}', template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)


    def display_statistics(self, df, stat_col):
         if df is None or stat_col not in df or not pd.api.types.is_numeric_dtype(df[stat_col]):
              st.warning(f"Cannot calculate stats for non-numeric column '{stat_col}'.")
              return
         st.subheader(f"Statistics for '{stat_col}'")
         col1, col2, col3, col4 = st.columns(4)
         try:
             col1.metric("Minimum", f"{df[stat_col].min():.2f}")
             col2.metric("Maximum", f"{df[stat_col].max():.2f}")
             col3.metric("Average", f"{df[stat_col].mean():.2f}")
             col4.metric("Std Dev", f"{df[stat_col].std():.2f}")
         except Exception as e:
             st.error(f"Error calculating stats: {e}")

    def footer(self):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #ccc;'>Powered by Streamlit & Plotly</p>", unsafe_allow_html=True)

    def run(self):
        """Executes the dashboard page."""
        st.markdown('<div class="dashboard-dark-theme">', unsafe_allow_html=True) # Apply theme

        self.setup_header()
        self.load_data() # File upload in sidebar

        if self.df:
            selected_table_df = self.select_table() # Table select in sidebar

            if selected_table_df is not None and not selected_table_df.empty:
                 # Stats Selection in sidebar
                 with st.sidebar:
                     numeric_cols = selected_table_df.select_dtypes(include=np.number).columns.tolist()
                     if numeric_cols:
                         stat_col = st.selectbox("Select column for stats", numeric_cols, key="excel_stat_col")
                     else:
                         st.warning("No numeric columns for stats.")
                         stat_col = None

                 # Axis Selection in sidebar
                 x_col, y_col = self.select_axes(selected_table_df)

                 # --- Main Area ---
                 if stat_col: # Display stats if a valid column was selected
                     self.display_statistics(selected_table_df, stat_col)
                     st.markdown("---")

                 # Tabs for Table and Plots
                 tab1, tab2 = st.tabs(["📄 Data Table", "📈 Plots"])

                 with tab1:
                      # Use a non-interactive way to show selected table name if needed
                      # current_table_name = st.session_state.get('excel_table_select', 'Unknown')
                      # st.subheader(f"Selected Table: '{current_table_name}'")
                      st.dataframe(selected_table_df, use_container_width=True)

                 with tab2:
                     st.subheader("Visualizations")
                     if x_col and y_col:
                         with st.sidebar: # Keep graph type selection in sidebar
                            graph_type = st.radio("Select Graph Type", ('Scatter', 'Bar', 'Pie'), horizontal=True, key="excel_graph_type")

                         # Plotting logic based on selection
                         if graph_type == 'Scatter': self.create_scatter_plot(selected_table_df, x_col, y_col)
                         elif graph_type == 'Bar': self.create_bar_plot(selected_table_df, x_col, y_col)
                         elif graph_type == 'Pie':
                             if pd.api.types.is_numeric_dtype(selected_table_df[y_col]):
                                 self.create_pie_chart(selected_table_df, x_col, y_col)
                             else: st.warning(f"Pie chart needs numeric values ('{y_col}' is not).")
                     else: st.warning("Select X and Y axes in sidebar.")
            elif selected_table_df is not None: # Table exists but is empty
                 st.warning("Selected Excel table is empty.")
        else:
            st.info("Upload an Excel file using the sidebar to view the dashboard.")


        self.footer()
        st.markdown('</div>', unsafe_allow_html=True) # Close theme div

