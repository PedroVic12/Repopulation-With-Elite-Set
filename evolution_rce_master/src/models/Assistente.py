import os
import pyttsx3
import speech_recognition as sr
import webbrowser
import wikipedia
from subprocess import call
import os
import pyautogui

wikipedia.set_lang("pt")


class AssistentePyAutoController:
    def __init__(self) -> None:
        pass

    def iniciar_tarefa_linux(self):
        # pyautogui.hotkey("ctrl", "alt", "t")
        # pyautogui.typewrite("ls")
        # pyautogui.press("enter")
        pyautogui.press("winleft")
        pyautogui.typewrite("terminal")
        pyautogui.press("enter")

    def comando_linux(self, command):
        os.system(command)


class AssistenteVirtual:
    def __init__(self):
        self.engine = pyttsx3.init("espeak")  # Usando espeak para Linux
        self.engine.setProperty("voice", self.engine.getProperty("voices")[1].id)
        self.py_controller = AssistentePyAutoController()

    def falar(self, audio):
        self.engine.say(audio)
        self.engine.runAndWait()

    def listar_vozes(self):
        vozes = self.engine.getProperty("voices")
        for voz in vozes:
            print("Id: ", voz.id)
            print("Nome: ", voz.name)
            print("Lang: ", voz.languages)

            # se for pt-br
            if "pt-br" in voz.languages:
                print("Usando voz pt-br")
                self.engine.setProperty("voice", voz.id)
                break

    def ouvir(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Ouvindo...")
            r.pause_threshold = 1
            audio = r.listen(source)
            try:
                print("Reconhecendo...")
                comando = r.recognize_google(audio, language="pt-BR")
                print("Usuário falou:" + comando + "\n")
            except Exception as e:
                print(e)
                self.falar("Eu não entendi mestre pedro, pode repetir?")
                return "None"
            return comando

    def executar_comando(self, comando):
        comando = comando.lower()
        if "wikipédia" in comando:
            self.falar("Procurando na Wikipedia ...")
            comando = comando.replace("wikipédia", "")
            comando = comando.replace("Procure na", "")
            resultados = wikipedia.summary(comando, sentences=2)
            self.falar("De acordo com a Wikipédia")
            self.falar(resultados)
        elif "como você vai" in comando:
            self.falar("Olá amigo, eu vou bem, obrigado por perguntar")

        elif "tarefa linux" in comando:
            self.falar("Iniciando tarefa linux")
            self.py_controller.iniciar_tarefa_linux()

        elif "abrir youtube" in comando:
            self.falar("Abrindo o Navegador com o youtube")
            webbrowser.open_new_tab("youtube.com")
        elif "abrir o google" in comando:
            self.falar("Abrindo o google")
            webbrowser.open_new_tab("www.google.com")
        elif "abrir github" in comando:
            self.falar("Abrindo o github")
            webbrowser.open_new_tab("github.com")
        elif "abrir o stackoverflow" in comando:
            self.falar("Abrindo o stackoverflow")
            webbrowser.open("stackoverflow.com")
        elif "abrir o spotify" in comando:
            self.falar("Abrindo o spotify")
            pyautogui.press("winleft")
            pyautogui.typewrite("spotify")
            pyautogui.press("enter")
        elif "abrir a calculadora" in comando:
            self.falar("Abrindo a calculadora")
            call(["gnome-calculator"])  # Usando comando para calculadora no Linux
        elif "abrir pasta home" in comando:
            self.falar("Abrindo a pasta Home")
            webbrowser.open("file:///home/")
        elif "executar comando" in comando:
            self.falar("Qual comando você deseja executar?")
            comando_terminal = self.ouvir()
            if comando_terminal != "None":
                self.falar(f"Executando comando: {comando_terminal}")
                call(comando_terminal, shell=True)
        elif "comando linux" in comando:
            self.falar("Qual comando você deseja executar?")
            comando_terminal = self.ouvir()
            if comando_terminal != "None":
                comando_terminal = comando_terminal.lower()
                self.falar(f"Executando comando: {comando_terminal}")
                self.py_controller.comando_linux(comando_terminal)

        elif "tchau" in comando:
            self.falar("Tchau Tchau")
            exit(0)


if __name__ == "__main__":
    assistente = AssistenteVirtual()
    assistente.listar_vozes()
    assistente.falar("Amigo foi ativado ")
    assistente.falar("Como eu posso te ajudar?")
    while True:
        comando = assistente.ouvir()
        if comando != "None":
            assistente.executar_comando(comando)
