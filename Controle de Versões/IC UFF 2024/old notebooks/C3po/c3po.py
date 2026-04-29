import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import PIL
import os

GEMINI_KEY = "AIzaSyAPAFeexSmww1GOHMAQ0fWsHqoSlIppnDI"
genai.configure(api_key=GEMINI_KEY)


class C3PoAssisstente:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.speaker = pyttsx3.init()

    def ouvir_comando_de_voz(self):
        with sr.Microphone() as source:
            print("Diga algo...")
            self.speaker.say("Diga algo...")
            self.speaker.runAndWait()
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)

        try:
            texto = self.recognizer.recognize_google(audio, language="pt-BR")
            print("Você disse:", texto)
            return texto
        except sr.UnknownValueError:
            print("Não foi possível entender o áudio.")
            return ""
        except sr.RequestError as e:
            print(
                "Erro ao solicitar resultados do serviço de reconhecimento de voz; {0}".format(
                    e
                )
            )
            return ""

    def falar_resposta(self, resposta):
        self.speaker.say(resposta)
        self.speaker.runAndWait()

    def interpretar_comando(self, comando):
        if "corrigir texto" in comando:
            texto_ocr = "Texto obtido por OCR"
            texto_vision = "Texto obtido por visão computacional"
            texto_corrigido = self.c3poCorrigeTexto(texto_ocr, texto_vision)
            self.falar_resposta(texto_corrigido)
        elif "ver imagem" in comando:
            img_path = "caminho/para/imagem.jpg"
            prompt_cliente = "Descreva a imagem"
            descricao_imagem = self.modeloVisaoComputacional(img_path, prompt_cliente)
            self.falar_resposta(descricao_imagem)
        else:
            self.falar_resposta("Desculpe, não entendi o comando.")

    def modeloTextoGenerativo(self, txt):
        model_TextGenerator = genai.GenerativeModel("gemini-pro")
        response = model_TextGenerator.generate_content(txt)
        return response.text

    def c3poCorrigeTexto(self, texto_ocr, texto_vision):
        texto_completo = texto_ocr + texto_vision

        _prompt = """ 
        Corrija o texto para extrair a data, local pegando seu logradouro ou CEP ou nome do estabelecimento, produtos com apenas o nome separando com um \n e total da nota fiscal em cada linha com os rótulos como Data: Local: Produtos: Total:
            """

        texto_corrigido = self.modeloTextoGenerativo(
            texto_completo + "\n\n\n\n" + _prompt
        )

        print("\n\nC3PO: Responde\n")
        return texto_corrigido

    def modeloVisaoComputacional(self, img_path, prompt_cliente):
        model_VisaoComputacional = genai.GenerativeModel("gemini-pro-vision")

        imagem = PIL.Image.open(img_path)

        response = model_VisaoComputacional.generate_content(imagem)
        print("IMG= ", response.text)
        response_text = model_VisaoComputacional.generate_content(
            [prompt_cliente, imagem]
        )
        result = response_text.resolve()
        return response.text


# Exemplo de uso
c3po = C3PoAssisstente()

# Usando voz para enviar comando
comando = c3po.ouvir_comando_de_voz()

# Interpretando o comando e executando a ação correspondente
c3po.interpretar_comando(comando)
