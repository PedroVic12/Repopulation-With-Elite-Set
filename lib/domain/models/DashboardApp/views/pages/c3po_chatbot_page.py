
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import numpy as np
import matplotlib.pyplot as plt
import io
import os
# Optional, for audio speedup if you install it later:
# try:
#     from pydub import AudioSegment
#     PYDUB_AVAILABLE = True
# except ImportError:
#     PYDUB_AVAILABLE = False


from .config import API_KEY, DEFAULT_MODEL, historico_c3po_inicial, CSS

from .graficos import funcao_seno, sinal_pwm, circuito_rc

# --- Backend AI and TTS Class ---
class AssistenteGenAI:
    """Handles interactions with the Gemini AI model and TTS generation."""
    def __init__(self, model_name=DEFAULT_MODEL, api_key=None):
        self.model_name = model_name
        self.api_key = api_key # Store the key if needed elsewhere, though genai config is global
        self._configure_genai_settings()
        self._load_model()

    def _configure_genai_settings(self):
        """Sets up generation and safety settings."""
        # Note: genai.configure(api_key=...) should already be done outside
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.4, # Adjusted for more consistent C3PO persona
            top_k=40,
            top_p=0.95,
            candidate_count=1,
        )
        self.safety_settings = [
             {"category": c, "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
             for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                       "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
        ]

    def _load_model(self):
        """Loads the generative model."""
        try:
            # Add system instruction for better persona consistency
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction="Você é C-3PO do Star Wars, um droide de protocolo fluente em mais de seis milhões de formas de comunicação, incluindo português do Brasil. Você é formal, um pouco ansioso, mas extremamente leal e prestativo ao seu Mestre Pedro. Use ocasionalmente exclamações como 'Oh, céus!', 'Pelo criado Anakin!', 'Que maravilha!'. Refira-se a Pedro como 'Mestre Pedro'. Mantenha as respostas concisas e úteis."
            )
            print(f"Modelo Gemini '{self.model_name}' carregado com sucesso.")
        except Exception as e:
            st.error(f"🔴 Erro crítico ao carregar o modelo Gemini '{self.model_name}': {e}")
            print(f"Erro ao carregar o modelo Gemini '{self.model_name}': {e}")
            self.model = None
            st.stop() # Stop if model fails to load

    def generate_audio_gtts(self, text: str) -> tuple[bytes | None, str | None]:
        """
        Generates audio bytes from text using gTTS.
        Returns (audio_bytes, error_message).
        """
        if not text:
            return None, "Nenhum texto fornecido para geração de áudio."
        print("Gerando áudio para:", text[:50] + "...") # Log start

        try:
            tts = gTTS(text=text, lang='pt', slow=False, tld='com.br')
            audio_bytes_io = io.BytesIO()
            tts.write_to_fp(audio_bytes_io)
            audio_bytes_io.seek(0)
            audio_bytes = audio_bytes_io.read()
            audio_bytes_io.close()

            # --- Optional Speedup using pydub (if installed) ---
            # if PYDUB_AVAILABLE:
            #     try:
            #         audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            #         # Adjust speed factor as needed (e.g., 1.2 for 20% faster)
            #         sped_up_audio = audio_segment.speedup(playback_speed=1.2)
            #         output_io = io.BytesIO()
            #         sped_up_audio.export(output_io, format="mp3")
            #         output_io.seek(0)
            #         audio_bytes = output_io.read()
            #         output_io.close()
            #         print("Áudio acelerado com sucesso (pydub).")
            #     except Exception as speed_e:
            #         print(f"Aviso: Falha ao acelerar áudio com pydub: {speed_e}. Usando velocidade original.")
            # else:
            #      print("Aviso: pydub não instalado. Para áudio mais rápido, 'pip install pydub'.")
            # --- End Optional Speedup ---

            print("Áudio gerado com sucesso (em memória).")
            return audio_bytes, None

        except Exception as e:
            error_msg = f"Erro ao gerar áudio com gTTS: {e}"
            print(error_msg)
            return None, error_msg

    def send_to_gemini(self, prompt_text=None, history=None) -> tuple[str | None, dict | None, str | None]:
        """
        Sends text prompt to Gemini and returns the response.
        (Image input part removed as it's not used by the frontend)
        Returns (response_text, ai_history_entry, error_message).
        """
        if not self.model:
            return None, None, "Modelo de IA não carregado."

        if not prompt_text:
             return None, None, "Nenhum prompt de texto fornecido."

        # Structure the prompt for the API
        parts = [{"text": prompt_text}]
        current_message_content = [{"role": "user", "parts": parts}]
        full_conversation = (history or []) + current_message_content # Combine history + current prompt

        print(f"Enviando para Gemini (Histórico: {len(history or [])} msgs): {prompt_text[:50]}...") # Log request

        try:
            # Use the model's chat capabilities if possible (maintains context better)
            # For simplicity here, we'll use generate_content which requires passing full history
            response = self.model.generate_content(
                contents=full_conversation, # Send the whole conversation
                stream=False # Get the full response at once
            )
            response.resolve() # Ensure the response is fully processed

            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                ai_response_for_history = {"role": "model", "parts": [{"text": response_text}]}
                print(f"Gemini respondeu: {response_text[:50]}...") # Log response
                return response_text, ai_response_for_history, None
            else:
                 # Handle blocked or empty responses
                 finish_reason = "N/A"
                 block_reason = "N/A"
                 safety_feedback_str = "N/A"
                 if hasattr(response, 'prompt_feedback'):
                     safety_feedback_str = str(response.prompt_feedback)
                 if response.candidates:
                    candidate = response.candidates[0]
                    finish_reason = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
                    if finish_reason == 'SAFETY' and candidate.safety_ratings:
                        block_reason = candidate.safety_ratings[0].category.name if hasattr(candidate.safety_ratings[0].category, 'name') else str(candidate.safety_ratings[0].category)

                 error_msg = f"Nenhuma resposta de texto recebida da IA. Razão: {finish_reason}. Bloqueio: {block_reason}. Feedback: {safety_feedback_str}"
                 print(f"Erro Gemini: {error_msg}")
                 # Return the error message as the text response to show the user
                 return f"🤖 Oh céus! Não posso processar isso. ({error_msg})", None, error_msg

        except Exception as e:
            error_msg = f"Erro ao comunicar com a API Gemini: {e}"
            print(f"Erro Gemini: {error_msg}")
            # Return the error message as the text response
            return f"🤖 Houve um erro: {error_msg}", None, error_msg


# --- Frontend Functions ---
def ChatbotScreen(assistente: AssistenteGenAI):
    """Renders the chat interface and handles interactions."""

    #st.image("https://media1.tenor.com/m/yYZMAqky0HYAAAAC/c3po-star-wars.gif", width=150) # Animated GIF
    st.image("https://moseisleychronicles.wordpress.com/wp-content/uploads/2015/11/untitled-215.gif", width=650)
    st.title("Assistente C3PO")
    st.caption("Seu droide de protocolo pessoal para produtividade e mais.")

    # --- Chat History Display ---
    # Use a container with specific height and scrollbar for chat history
    chat_history_container = st.container(height=500, border=False)
    with chat_history_container:
        for i, message in enumerate(st.session_state.messages):
            role = message["role"]
            # Ensure parts exist and extract text
            display_text = ""
            if "parts" in message and isinstance(message["parts"], list):
                 display_text = "".join(p.get("text", "") for p in message["parts"] if isinstance(p, dict))

            with st.chat_message(name=role, avatar="🤖" if role == "model" else "🧑‍🚀"):
                st.markdown(display_text)
                # Add TTS button only for non-empty model messages
                if role == "model" and display_text and not display_text.startswith("🤖"): # Avoid TTS for error messages starting with emoji
                    tts_button_key = f"tts_{i}_{role}" # More specific key
                    if st.button(f"🔊 Ouvir", key=tts_button_key, help="Ouvir a resposta do C3PO"):
                        with st.spinner("Gerando áudio... Por favor, aguarde."):
                            audio_bytes, error = assistente.generate_audio_gtts(display_text)
                            if error:
                                st.toast(f"Erro no TTS: {error}", icon="🚨") # Use toast for non-blocking error
                            elif audio_bytes:
                                # Store audio and rerun to display it outside the loop
                                st.session_state.current_audio_bytes = audio_bytes
                                st.session_state.current_audio_key = tts_button_key # Store key to avoid re-playing on unrelated reruns
                                st.rerun()

    # --- Audio Player ---
    # Display audio player ONLY if the corresponding button was just clicked
    # And clear it after it's presumably played or if another button is clicked
    if 'current_audio_bytes' in st.session_state and st.session_state.current_audio_bytes:
        # Check if the last button clicked corresponds to this audio (simple check)
        # A more robust way might involve checking widget state, but this is often sufficient
         if 'last_triggered_button_key' not in st.session_state or st.session_state.last_triggered_button_key == st.session_state.get('current_audio_key'):
              st.audio(st.session_state.current_audio_bytes, format='audio/mp3', start_time=0)
         # Clear the audio after displaying it once to prevent re-playing on next rerun
         st.session_state.current_audio_bytes = None
         st.session_state.current_audio_key = None


    # --- User Input ---
    user_prompt = st.chat_input("Digite sua mensagem para o C3PO:")
    if user_prompt:
        print(f"Usuário digitou: {user_prompt[:50]}...")
        # Append user message to state immediately for display
        st.session_state.messages.append({"role": "user", "parts": [{"text": user_prompt}]})
        # Clear any pending audio playback before showing spinner/getting response
        st.session_state.current_audio_bytes = None
        st.session_state.current_audio_key = None
        st.rerun() # Rerun to show user message instantly

# Separate function to handle the Gemini response after the user message is shown
def handle_gemini_response(assistente: AssistenteGenAI):
    # Check if the last message is from the user and hasn't been processed yet
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        if 'last_processed_user_message' not in st.session_state or st.session_state.last_processed_user_message != st.session_state.messages[-1]:

            last_user_message = st.session_state.messages[-1]
            st.session_state.last_processed_user_message = last_user_message # Mark as being processed

            with st.spinner("C3PO está calculando a resposta..."):
                # Send history *excluding* the last user message (which is the current prompt)
                response_text, ai_history_entry, error = assistente.send_to_gemini(
                    prompt_text=last_user_message["parts"][0]["text"],
                    history=st.session_state.messages[:-1] # Pass history BEFORE the current user msg
                )

            # If Gemini returned a valid response structure, add it to history
            if ai_history_entry:
                st.session_state.messages.append(ai_history_entry)
            # If there was an error but Gemini generated an error message text
            elif response_text and not ai_history_entry:
                 st.session_state.messages.append({"role": "model", "parts": [{"text": response_text}]})
            # If there was a critical error and no text response
            elif error:
                 st.session_state.messages.append({"role": "model", "parts": [{"text": f"🤖 Oh não! Erro interno: {error}"}]})

            # Rerun to display the new AI response
            st.rerun()


# --- Main Page Function ---
def C3poChatbotPage():
    """Sets up the main page layout and logic."""
    
    #st.set_page_config(page_title="C3PO Assistente", layout="wide", page_icon="🤖")

    # --- Apply CSS ---
    st.markdown(CSS, unsafe_allow_html=True)

    # --- Initialize Session State ---
    if 'messages' not in st.session_state:
        # Start with a fresh copy of the initial history
        st.session_state.messages = list(historico_c3po_inicial)
        print("Histórico de chat inicializado.")
    if 'current_audio_bytes' not in st.session_state:
        st.session_state.current_audio_bytes = None
    if 'current_audio_key' not in st.session_state:
        st.session_state.current_audio_key = None
    if 'last_processed_user_message' not in st.session_state:
        st.session_state.last_processed_user_message = None

    # --- Instantiate Assistant ---
    # Pass the configured API key (already checked at the top)
    assistente = AssistenteGenAI(api_key=API_KEY)
    if not assistente.model: # Check if model loaded successfully
         st.error("🔴 Modelo de IA não pôde ser carregado. A aplicação não pode continuar.")
         st.stop()

    # --- Page Layout ---
    col1, col2 = st.columns([2, 1]) # Chat takes more space

    with col1:
        # Render the chat screen (displays history, handles input)
        ChatbotScreen(assistente)
        # Handle the response generation *after* potential input/rerun
        handle_gemini_response(assistente)


    with col2:
        st.header("📊 Dashboard Simples")
        st.write("Visualização de dados de exemplo.")
        
        # Criação das abas
        tab1, tab2, tab3 = st.tabs(["Funções Seno e Cosseno", "Sinal PWM", "Resposta de Circuito RC"])
        with tab1:
            st.subheader("Funções Seno e Cosseno")
            funcao_seno()

        with tab2:
            st.subheader("Sinal PWM")
            sinal_pwm()

        with tab3:
            st.subheader("Resposta de Circuito RC")
            circuito_rc()

# --- Run the App ---
if __name__ == "__main__":
    C3poChatbotPage()