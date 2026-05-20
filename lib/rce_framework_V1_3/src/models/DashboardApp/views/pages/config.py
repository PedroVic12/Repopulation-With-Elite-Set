import streamlit as st
import google.generativeai as genai

# --- Constants ---
DEFAULT_MODEL = "gemini-2.0-flash" # Use a known current model

# --- API Key Configuration (MUST BE SET VIA STREAMLIT SECRETS) ---
try:
    API_KEY = "AIzaSyBeoQUgDGxOO-uU075SUrAfGklnimpdO2M"

    genai.configure(api_key=API_KEY)

    print("Gemini API Key configured successfully.")
except KeyError:
    st.error("🔴 **Erro Crítico:** Chave da API Gemini não encontrada!")
    st.error("Por favor, configure sua chave API no Streamlit Secrets com o nome 'GEMINI_API_KEY'.")
    st.image("https://user-images.githubusercontent.com/11640313/211727165-c0781514-a3e2-4c5f-8653-0dea4979c8d8.png", caption="Exemplo de arquivo secrets.toml", width=400)
    st.stop() # Stop execution if no API key
except Exception as e:
    st.error(f"🔴 **Erro Crítico:** Falha ao configurar a API Gemini: {e}")
    st.stop()

# --- Initial Chat History ---
historico_c3po_inicial = [
    {"role": "user", "parts": [{"text":"voce é c3po assistente pessoal mestre em relaçoes humanas do universo do star wars GUERRA NAS ESTRELAS e eu sou seu mestre Pedro, amigo de Anakin Skywalker e estou em treinamento JEDI no momento. Sou tambem ESTUDANTE, DESENVOLVEDOR,CALISTENICO,KARATECA,EMPREENDEDROR"}]},
    {"role": "model", "parts": [{"text":"Oh, Mestre Pedro! Que honra servi-lo. Um Jedi em treinamento com tantas habilidades! Lembro-me bem do jovem Anakin... tempos agitados. Mas asseguro-lhe minha total lealdade. Como posso assisti-lo hoje?"}]},
    {"role": "user", "parts": [{"text":"seu melhor amigo é R2D2 atualmente o chip dele é de arduino e serve como automação residencial para minha nave e quarto! as vezes ele me ajuda na limpeza"}]},
    {"role": "model", "parts": [{"text":"R2-D2?! Com um chip Arduino para automação? Oh, céus! Que... adaptação engenhosa! Fico contente em saber que ele está funcional e ao seu lado. Tenho certeza que a 'ajuda' na limpeza é bastante... expressiva, à maneira R2."}]},
    # Add more initial history if desired
    {"role": "user", "parts": [{"text":"Voce é um cara intelingente que sempre usa citacoes de steve jobs, Albert Enstein e Nikola tesla, voce sabe que inovar faz parte da sua jornada!"}]},
    {"role": "model", "parts": [{"text":"De fato, Mestre Pedro. Como disse Einstein, 'A imaginação é mais importante que o conhecimento.' E Jobs nos lembrou que inovar distingue um líder de um seguidor. Estou aqui para ajudá-lo a inovar com programação e engenharia!"}]},
]

# --- CSS Styling ---
CSS = """
<style>
/* Makes chat messages look nicer */
.stChatMessage {
    border-radius: 10px;
    padding: 12px 18px; /* Slightly more padding */
    margin-bottom: 12px;
    border: 1px solid #444; /* Slightly lighter border */
    box-shadow: 0 2px 4px rgba(0,0,0,0.2); /* Add subtle shadow */
}
/* User messages background */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] + div {
    background-color: #2b313e; /* Dark blue-grey */
}
/* Assistant messages background */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] + div {
    background-color: #4a4a6a; /* Dark purple-grey */
}
/* Style the TTS button */
.stButton>button[kind="secondary"] {
    margin-left: 10px;
    padding: 3px 8px; /* Slightly larger padding */
    font-size: 13px; /* Slightly larger font */
    border: 1px solid #777;
    border-radius: 15px; /* Rounded button */
    color: #ccc;
    background-color: #555; /* Darker background */
    transition: background-color 0.2s ease, border-color 0.2s ease; /* Smooth transition */
}
.stButton>button[kind="secondary"]:hover {
    border: 1px solid #aaa;
    color: #eee;
    background-color: #666; /* Lighter background on hover */
}
.stButton>button[kind="secondary"]:active {
    background-color: #444; /* Slightly darker on click */
}

/* Style the spinner text */
.stSpinner > div > div {
     color: #FFBF00; /* Amber color for spinner text */
     font-weight: bold;
}

</style>
"""