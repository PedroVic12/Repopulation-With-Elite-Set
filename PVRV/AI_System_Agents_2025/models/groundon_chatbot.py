
import os
from google import genai

#

#os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"  # Substitua pela sua chave de API do Google


API_KEY = "AIzaSyAw-JTE-fF5IJ-uoTiqdkswxXOK4nnTw2w"

client = genai.Client(
    api_key=API_KEY,
)


for model in client.models.list():

    if "models/gemini"  in model.name:
        print(model.name)  # Exibe o nome do modelo
        print(model.description)  # Exibe a descrição do modelo
        print("\n\n")
        #print(model.supported_generation_types)  # Exibe os tipos de geração suportados
        #print(model.supported_input_types)  # Exibe os tipos de entrada suportados
        #print(model.supported_output_types)  # Exibe os tipos de saída suportados


modelo = "gemini-2.0-flash"
user_prompt = "Como posso otimizar o desempenho de um algoritmo genético para resolver problemas complexos?"
resposta = client.models.generate_content(
    model=modelo,
    contents= user_prompt,

)


chat = client.chats.create(model=modelo)

resposta = chat.send_message("Oi, tudo bem?")

resposta.text


resposta = chat.send_message("O que é Inteligência Artificial?")

resposta.text


resposta = chat.send_message("Você é um assistente pessoal e você sempre responde de forma sucinta. O que é Inteligência Artificial?")

resposta.text


from google.genai import types

chat_config = types.GenerateContentConfig(
    system_instruction = "Você é um assistente pessoal e você sempre responde de forma sucinta.",
)

chat = client.chats.create(model=modelo, config=chat_config)

from google.genai import types

chat_config = types.GenerateContentConfig(
    system_instruction = "Você é um assistente pessoal e você sempre responde de forma sucinta.",
)

chat = client.chats.create(model=modelo, config=chat_config)


chat.get_history()


prompt = input("Esperando prompt: ")

while prompt != "fim":
    resposta = chat.send_message(prompt)
    print("Resposta: ", resposta.text)
    print("\n")
    prompt = input("Esperando prompt: ")


chat_config_2 = types.GenerateContentConfig(
    system_instruction = "Você é um assistente pessoal que sempre responde de forma muito sarcástica.",
)

chat_2 = client.chats.create(model=modelo, config=chat_config_2)

resposta = chat_2.send_message("O que é computação quântica?")

resposta.text