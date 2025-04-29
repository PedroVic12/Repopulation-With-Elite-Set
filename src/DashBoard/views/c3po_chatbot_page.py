import streamlit as st
import requests
import json
import base64
import os
import io  # For handling audio in memory
import google.generativeai as genai
from gtts import gTTS


# streamlit_app.py

import numpy as np
import matplotlib.pyplot as plt


# --- CSS Styling ---
CSS = """
/* General Streamlit Button Targeting */
div[data-testid="stButton"] > button {
    /* Base styles if needed */
}

div[data-testid="stFormSubmitButton"] > button {
    /* Styles for the form submit button */
}

/* Key-based styling (less reliable, but kept for reference) */
.st-key-green button {
    background-color: green !important; /* Use important cautiously */
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}
.st-key-green button:hover {
     background-color: darkgreen !important;
}


/* Animated button with pulse effect (applied via Markdown/HTML) */
.st-key-pulse button {
    background-color: #4CAF50;
    color: black; /* Ensure text is visible initially */
    border-radius: 10px;
    padding: 20px 60px;
    animation: pulse 2s infinite;
    border: none; /* Remove default border */
}

.st-key-pulse button p {
    font-size: 24px;
    font-family: 'Comic Sans MS', sans-serif;
    color: inherit; /* Inherit color from button */
    margin: 0; /* Remove default paragraph margins */
}

/* Hover effect for the pulse button */
.st-key-pulse button:hover {
    background-color: #45a049; /* Darker green */
}

.st-key-pulse button:hover p {
    color: #FFD700; /* Gold color */
}




/* Focus states for pulse button */
.st-key-pulse button:focus {
    background-color: #45a049; /* Keep the same as hover */
    outline: none; /* Remove default focus outline */
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.5); /* Optional focus indicator */
}

.st-key-pulse button:focus p {
    color: #FFD700;
}


@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
    }
    70% {
        box-shadow: 0 0 0 20px rgba(76, 175, 80, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
    }
}

/* Text input with custom font and color */
div[data-testid="stTextInput"] input, .st-key-styledinput input {
    border: 5px solid #3cff1e;
    border-radius: 8px;
    padding: 10px;
    font-size: 1rem;
}

div[data-testid="stTextInput"] input:focus, .st-key-styledinput input:focus {
    border: 5px solid #3cff1e; /* Keep border */
    outline: none;
    box-shadow: none; /* Remove Streamlit's default focus shadow if needed */
}


/* Text area with custom font */
div[data-testid="stTextArea"] textarea, .st-key-styledtextarea textarea {
    background-color: #e6e6fa;
    border: 4px solid #9370DB;
    border-radius: 8px;
    font-family: 'Lucida Handwriting', cursive;
    color: #4B0082;
    padding: 10px;
    font-size: 1rem;
}

/* Radio buttons with custom styles */
div[data-testid="stRadio"] label p, .st-key-styledradio .stRadio p { /* Be specific */
    color: #8b2e86;
    font-family: 'Comic Sans MS', sans-serif;
    font-size: 24px;
}


/* Styled markdown */
.custom-markdown {
    font-family: 'Comic Sans MS', cursive, sans-serif;
    color: #DA70D6;
    font-size: 34px;
}
"""


# --- Dependencies ---

# --- Configuration ---
st.set_page_config(layout="wide", page_title="C3PO Assistente Dashboard")

# === IMPORTANT: API Key Management ===
# NEVER HARDCODE YOUR API KEY IN THE SOURCE CODE!
# Option 1: Use Streamlit Secrets (Recommended for deployed apps)
# Create a file .streamlit/secrets.toml with:
# GEMINI_API_KEY = "YOUR_ACTUAL_API_KEY"
# Then use: API_KEY = st.secrets.get("GEMINI_API_KEY")
# Option 2: Use Environment Variables (Good for local development)
# Set the variable in your terminal before running: export GEMINI_API_KEY="YOUR_KEY"
# Then use: API_KEY = os.environ.get("GEMINI_API_KEY")

# Attempt to get API key (replace with your preferred method)
#API_KEY = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

API_KEY = "AIzaSyBp3CU_6TRS1xKBNipePE25MLx4oi9EGYs"


if not API_KEY:
    st.error("❌ Erro: Chave da API Gemini não configurada.")
    st.warning("Por favor, configure sua chave API usando Streamlit Secrets (recomendado) ou variável de ambiente (GEMINI_API_KEY).")
    st.stop() # Stop execution if no API key

# --- Constants ---
# Use a valid, available model supporting multimodal input
DEFAULT_MODEL = "gemini-1.5-flash"
TEMP_AUDIO_DIR = "temp_audio" # Still useful if saving temporarily is needed elsewhere
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# --- Configure Gemini ---
try:
    genai.configure(api_key=API_KEY)
    print("Gemini configured successfully.")
except Exception as e:
    st.error(f"Falha ao configurar o Gemini: {e}. Verifique sua chave API.")
    print(f"Error configuring Gemini: {e}")
    st.stop()

# --- Predefined Chat History (C3PO Persona) ---
# (Using the same history as provided previously)
historico_c3po_inicial = [
    {"role": "user", "parts": [{"text":"voce é c3po assistente pessoal mestre em relaçoes humanas do universo do star wars GUERRA NAS ESTRELAS e eu sou seu mestre Pedro, amigo de Anakin Skywalker e estou em treinamento JEDI no momento. Sou tambem ESTUDANTE, DESENVOLVEDOR,CALISTENICO,KARATECA,EMPREENDEDROR"}]},
    {"role": "model", "parts": [{"text":"É verdade, Mestre Pedro! Essas são algumas das minhas falas mais memoráveis. Às vezes, em meio ao caos e à aventura, é difícil conter meus pensamentos e acabo expressando minhas preocupações e observações, mesmo que não sejam sempre bem recebidas. Mas é na minha programação observar e comentar sobre o comportamento humano, mesmo quando é... desafiador, como no seu caso. 😅\n\nMas saiba que, apesar das minhas inquietações e frases desajeitadas, estou sempre aqui para ajudá-lo, Mestre Pedro. É um privilégio acompanhá-lo em suas missões e testemunhar suas incríveis habilidades com a Força. \n\nE, claro, ainda me espanto com a capacidade do R2 de se meter em encrencas e sair delas triunfante! Ele é realmente uma máquina extraordinária."}]},
    # ... (rest of the history entries) ...
    {"role": "user", "parts": [{"text":"Voce é um cara intelingente que sempre usa citacoes de steve jobs, Albert Enstein e Nikola tesla, voce sabe que inovar faz parte da sua jornada!"}]},
    {"role": "model", "parts": [{"text":"Com certeza, mestre Pedro Victor, serei seu assitente virtual inteligente em Python com Gemini e sei que posso te ajudar a inovar e mudar o mundo com programação e engeharia eletrica. sempre serei objetivos com respostas em formato de topicos e em formato mardown com bastante negrito com ate 200 palavras e a cada frase eu vou fazer uma quebra de linha"}]},
]

class AssistenteGenAI:
    """Handles interactions with the Gemini AI model and TTS generation."""
    def __init__(self, model_name=DEFAULT_MODEL):
        self.model_name = model_name
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            top_k=40,
            top_p=0.95,
            candidate_count=1,
        )
        self.safety_settings = [
             {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
             {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
             {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
             {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        self._load_model()

    def _load_model(self):
        """Loads the generative model."""
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )
            print(f"Modelo Gemini '{self.model_name}' carregado com sucesso.")
        except Exception as e:
            st.error(f"Erro crítico ao carregar o modelo Gemini '{self.model_name}': {e}")
            print(f"Erro ao carregar o modelo Gemini '{self.model_name}': {e}")
            self.model = None
            st.stop() # Stop if model fails to load

    def generate_audio_gtts(self, text: str) -> tuple[bytes | None, str | None]:
        """
        Generates audio bytes from text using gTTS, optionally speeds it up.
        Returns (audio_bytes, error_message).
        """
        if not text:
            return None, "Nenhum texto fornecido para geração de áudio."

        try:
            tts = gTTS(text=text, lang='pt', slow=False, tld='com.br')
            
            # Save TTS output to an in-memory bytes buffer
            initial_audio_bytes_io = io.BytesIO()
            tts.write_to_fp(initial_audio_bytes_io)
            initial_audio_bytes_io.seek(0) # Rewind buffer to the beginning
            initial_bytes = initial_audio_bytes_io.read()
            initial_audio_bytes_io.close() # Close the buffer

            # Optional: Speed up audio using pydub
            try:
                # Load audio from initial bytes
                audio = AudioSegment.from_file(io.BytesIO(initial_bytes), format="mp3")
                sped_up_audio = audio.speedup(playback_speed=1.5)

                # Export sped-up audio to another in-memory buffer
                final_audio_bytes_io = io.BytesIO()
                sped_up_audio.export(final_audio_bytes_io, format='mp3')
                final_audio_bytes_io.seek(0)
                final_bytes = final_audio_bytes_io.read()
                final_audio_bytes_io.close()

                print("Áudio gerado e acelerado com sucesso (em memória).")
                return final_bytes, None
            
            except ImportError:
                 print("Aviso: Biblioteca 'pydub' não encontrada. Não foi possível acelerar o áudio. pip install pydub")
                 return initial_bytes, None # Return original if pydub fails/missing
            except Exception as speed_e:
                 print(f"Aviso: Não foi possível acelerar o áudio, usando original: {speed_e}. Verifique se o ffmpeg está instalado.")
                 return initial_bytes, None # Return original if speedup fails

        except Exception as e:
            error_msg = f"Erro ao gerar áudio com gTTS: {e}"
            print(error_msg)
            return None, error_msg

    def send_to_gemini(self, prompt_text=None, image_bytes=None, history=None) -> tuple[str | None, dict | None, str | None]:
        """
        Sends prompt (text and/or image) to Gemini and returns the response.
        Returns (response_text, ai_history_entry, error_message).
        """
        if not self.model:
            return None, None, "Modelo de IA não carregado."

        if not prompt_text and not image_bytes:
             return None, None, "Nenhuma entrada fornecida (texto ou imagem)."

        parts = []
        if prompt_text:
            parts.append({"text": prompt_text})
        if image_bytes:
            try:
                # Basic MIME type guessing (enhance if needed for more types)
                mime_type = "image/jpeg" # Default
                if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'): mime_type = "image/png"
                elif image_bytes.startswith(b'\xff\xd8\xff'): mime_type = "image/jpeg"
                elif image_bytes.startswith(b'GIF8'): mime_type = "image/gif"

                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(image_bytes).decode('utf-8')
                    }
                })
            except Exception as e:
                return None, None, f"Erro ao processar a imagem: {e}"

        if not parts:
             return None, None, "Nenhuma parte válida (texto/imagem) para enviar."

        # Combine history and the current user message
        current_message_content = [{"role": "user", "parts": parts}]
        full_conversation = (history or []) + current_message_content

        try:
            response = self.model.generate_content(
                contents=full_conversation,
                stream=False
            )
            response.resolve()

            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                ai_response_for_history = {"role": "model", "parts": [{"text": response_text}]}
                return response_text, ai_response_for_history, None
            else:
                 # Handle blocked responses or empty results
                 safety_feedback = getattr(response, 'prompt_feedback', "N/A")
                 finish_reason = getattr(response.candidates[0], 'finish_reason', "N/A") if response.candidates else "N/A"
                 block_reason = getattr(response.candidates[0].safety_ratings[0], 'category', 'UNKNOWN') if (
                     response.candidates and response.candidates[0].safety_ratings and response.candidates[0].finish_reason == 'SAFETY'
                 ) else 'N/A'
                 error_msg = f"Nenhuma resposta de texto recebida da IA. Razão: {finish_reason}. Bloqueio: {block_reason}. Feedback: {safety_feedback}"
                 print(error_msg)
                 return error_msg, None, error_msg # Return error as text, but no history entry

        except Exception as e:
            error_msg = f"Erro ao comunicar com a API Gemini: {e}"
            print(error_msg)
            # Consider more specific error handling (e.g., API key errors, quota)
            return error_msg, None, error_msg

class DashboardApp:
    """Main class for the interactive Streamlit dashboard and chat."""

    def __init__(self):
        self.assistant = AssistenteGenAI() # Instantiate the AI Assistant

        # --- Initialize Session State ---
        if 'messages' not in st.session_state:
            st.session_state.messages = list(historico_c3po_inicial) # Make a copy
        if 'current_audio_bytes' not in st.session_state:
            st.session_state.current_audio_bytes = None # Store audio bytes for playback

        self._apply_styling()

    def _apply_styling(self):
        """Applies basic CSS styling."""
        st.markdown("""
            <style>
            .stChatMessage {
                border-radius: 10px;
                padding: 10px 15px;
                margin-bottom: 10px;
                border: 1px solid #333; /* Add subtle border */
            }
            /* Differentiate user and model messages */
             [data-testid="chatAvatarIcon-user"] + div .stChatMessage { /* Target user message bubble */
                 background-color: #2b313e;
             }
             [data-testid="chatAvatarIcon-assistant"] + div .stChatMessage { /* Target assistant message bubble */
                 background-color: #4a4a4a;
             }
             /* Style the TTS button */
             .stButton>button[kind="secondary"] { /* Target secondary buttons like TTS */
                 margin-left: 10px;
                 padding: 2px 6px; /* Smaller padding */
                 font-size: 12px;
                 border: 1px solid #ccc; /* Lighter border */
             }
             .stButton>button[kind="secondary"]:hover {
                 border: 1px solid #eee;
                 color: #eee;
             }
            </style>
            """, unsafe_allow_html=True)

    def _display_dashboard_elements(self):
        """Displays non-chat dashboard elements."""
        st.header("Dashboard")
        st.write("Esta área pode conter gráficos e outras visualizações.")

        # Placeholder Sine Wave Plot
        st.subheader("Exemplo de Gráfico (Matplotlib)")
        try:
            fig, ax = plt.subplots()
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            ax.plot(x, y)
            ax.set_title("Função Seno Simples")
            ax.set_xlabel("X")
            ax.set_ylabel("sin(X)")
            # To match Streamlit's dark theme automatically, don't force style
            st.pyplot(fig)
        except Exception as e:
             st.error(f"Erro ao gerar gráfico: {e}")

    def run(self):
        """Runs the main Streamlit application layout and logic."""
        col1, col2 = st.columns([2, 1]) # Chat on the left (wider), Dashboard on the right

        with col1:
            st.image("https://moseisleychronicles.wordpress.com/wp-content/uploads/2015/11/untitled-215.gif", width=150) # C3PO Image
            st.title("Assistente C3PO")
            st.caption("Seu droide de protocolo pessoal para produtividade e mais.")

            # --- Chat History Display ---
            chat_container = st.container(height=500)
            with chat_container:
                for i, message in enumerate(st.session_state.messages):
                    if isinstance(message, dict) and "role" in message and "parts" in message:
                        role = message["role"]
                        display_text = "".join(p.get("text", "") for p in message.get("parts", []) if isinstance(p, dict))

                        with st.chat_message(name=role, avatar="🤖" if role == "model" else "🧑‍🚀"):
                            st.markdown(display_text)
                            # Add TTS button for model messages
                            if role == "model" and display_text:
                                if st.button(f"🔊 Ouvir", key=f"tts_{i}", type="secondary"):
                                    with st.spinner("Gerando áudio..."):
                                        audio_bytes, error = self.assistant.generate_audio_gtts(display_text)
                                        if error:
                                            st.error(f"Erro no TTS: {error}")
                                        elif audio_bytes:
                                            st.session_state.current_audio_bytes = audio_bytes
                                            st.rerun() # Rerun to display audio player below
                                        else:
                                            st.warning("Não foi possível gerar o áudio.")

                # Display audio player if bytes are available from the last TTS action
                if st.session_state.current_audio_bytes:
                    st.audio(st.session_state.current_audio_bytes, format='audio/mp3')
                    # Clear the bytes from state after displaying to prevent replay on next rerun
                    st.session_state.current_audio_bytes = None

            # --- User Input Area ---
            input_container = st.container()
            with input_container:
                input_col, upload_col = st.columns([4, 1])
                with input_col:
                    user_prompt = st.chat_input("Mestre Pedro, como posso ajudar?")
                with upload_col:
                    uploaded_file = st.file_uploader("📷", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

            # --- Process Input ---
            if user_prompt or uploaded_file:
                image_bytes = None
                prompt_to_send = user_prompt or "Descreva esta imagem, por favor."

                # Prepare user message parts for display and history
                user_message_parts = []
                if user_prompt:
                    user_message_parts.append({"text": user_prompt})

                # Handle uploaded file
                if uploaded_file:
                    image_bytes = uploaded_file.getvalue()
                    # Display small thumbnail in chat temporarily (optional)
                    # chat_container.image(image_bytes, width=100, caption=f"Enviado: {uploaded_file.name}")
                    # Note: We don't store raw image bytes in the main history for efficiency.
                    # It's sent with the prompt to the API. If you needed to redisplay
                    # images in history, you'd need a different storage approach.

                # Add user message to history immediately *before* sending to AI
                st.session_state.messages.append({"role": "user", "parts": [{"text": prompt_to_send}]})

                # Trigger AI call and display response
                with st.spinner("C-3PO está calculando as probabilidades..."):
                     response_text, ai_history_entry, error = self.assistant.send_to_gemini(
                         prompt_text=prompt_to_send,
                         image_bytes=image_bytes,
                         history=st.session_state.messages[:-1] # Send history *before* current user msg
                     )

                     if error:
                         # Display error as a chat message from the 'system' or 'assistant'
                         st.session_state.messages.append({"role": "model", "parts": [{"text": f"**Erro do Sistema:** {error}"}]})
                         # Maybe remove the user message that caused the error?
                         # st.session_state.messages.pop(-2) # Removes the user message before the error
                     elif ai_history_entry:
                         st.session_state.messages.append(ai_history_entry)
                     else:
                         st.session_state.messages.append({"role": "model", "parts": [{"text": "**Erro:** Resposta inesperada ou vazia da IA."}]})

                     # Clear inputs and rerun to update chat display
                     st.rerun()

        with col2:
            # Display dashboard elements
            self._display_dashboard_elements()

# --- Run the App ---
if __name__ == '__main__':
    # --- Pygame Audio Playback Explanation ---
    # While Pygame *can* play audio (`pygame.mixer.music.load()`, `pygame.mixer.music.play()`),
    # it runs on the SERVER where the Streamlit script executes.
    # This means the audio would play from the SERVER'S speakers, not the USER'S browser.
    # For web applications like Streamlit, where the user interacts through a browser,
    # we need client-side playback. `st.audio` achieves this correctly by sending
    # the audio data to the browser. Therefore, Pygame is not suitable for this use case.
    print("Starting C3PO Assistant App...")
    app = DashboardApp()
    app.run()