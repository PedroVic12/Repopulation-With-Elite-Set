import os
from google import genai
from google.genai import types

class JarvisAI:
    def __init__(self, api_key, model="gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.chat = None

    def listar_modelos(self):
        """Lista todos os modelos disponíveis na API do Google Gemini."""
        modelos_disponiveis = []
        for model in self.client.models.list():
            if "models/gemini" in model.name:
                info = {
                    "name": model.name,
                    "description": model.description,
                    "supported_languages": model.supported_languages
                }
                modelos_disponiveis.append(info)
                print(info)
        return modelos_disponiveis

    def iniciar_chat(self, system_instruction="Você é um assistente pessoal inteligente e direto."):
        """Cria um novo chat com contexto personalizado."""
        chat_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )
        self.chat = self.client.chats.create(model=self.model, config=chat_config)
        print("Chat iniciado com personalidade definida.")

    def enviar_mensagem(self, mensagem):
        """Envia uma mensagem para o chat atual e retorna a resposta."""
        if not self.chat:
            raise Exception("Chat não iniciado. Use o método iniciar_chat primeiro.")
        resposta = self.chat.send_message(mensagem)
        print(f"Você: {mensagem}\nJarvisAI: {resposta.text}\n")
        return resposta.text

    def loop_conversa(self):
        """Inicia um loop de conversa até o usuário encerrar com 'fim'."""
        if not self.chat:
            self.iniciar_chat()
        prompt = input("Digite sua mensagem: ")
        while prompt.lower() != "fim":
            self.enviar_mensagem(prompt)
            prompt = input("Digite sua mensagem: ")
        print("Chat encerrado.")

    def ver_historico(self):
        """Exibe o histórico de mensagens do chat atual."""
        if not self.chat:
            raise Exception("Chat não iniciado. Use o método iniciar_chat primeiro.")
        historico = self.chat.get_history()
        if not historico:
            print("Nenhuma mensagem no histórico.")
            return
        print("===================================")
        print("Histórico de mensagens:")
        print("===================================")
        for msg in historico:
            print(f"JarvisAI: {msg}\n")

    def mudar_personalidade(self, estilo="direto"):
        """Muda o estilo de personalidade do JarvisAI."""
        estilos = {
            "direto": "Você é um assistente pessoal inteligente e direto.",
            "sarcastico": "Você é um assistente pessoal que sempre responde de forma muito sarcástica.",
            "educador": "Você é um professor paciente e atencioso.",
            "amigavel": "Você é um assistente amigável e descontraído."
        }
        instrucao = estilos.get(estilo, estilos["direto"])
        self.iniciar_chat(system_instruction=instrucao)
        print(f"Personalidade alterada para: {estilo}")

# Exemplo de uso
API_KEY = "AIzaSyAw-JTE-fF5IJ-uoTiqdkswxXOK4nnTw2w"

jarvis = JarvisAI(api_key=API_KEY)

# Lista os modelos disponíveis
#jarvis.listar_modelos()

# Inicia o chat com personalidade padrão
jarvis.iniciar_chat()

# Envia mensagens
jarvis.enviar_mensagem("Oi, tudo bem?")
jarvis.enviar_mensagem("O que é Inteligência Artificial?")

# Muda para personalidade sarcástica e envia outra mensagem
jarvis.mudar_personalidade(estilo="sarcastico, GEEK e inteligente")
#jarvis.enviar_mensagem("Qual a diferença entre IA e ML?")

jarvis.loop_conversa()





# Exibe o histórico de mensagens
jarvis.ver_historico()
