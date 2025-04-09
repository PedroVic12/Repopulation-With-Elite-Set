import pyautogui
import time
import streamlit as st

class PyDesktopController:
    def __init__(self):
        pass

    def click(self, x, y):
        """Clica na posição (x, y) da tela"""
        pyautogui.click(x, y)

    def write(self, text):
        pyautogui.write(text)

    def press(self, key):
        pyautogui.press(key)

    def hotkey(self, key):
        pyautogui.hotkey(key)

    def screenshot(self, filename):
        """Tira um screenshot da tela e salva com o nome especificado"""
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

    def locate_on_screen(self, image):
        """Localiza uma imagem na tela e retorna as coordenadas"""
        return pyautogui.locateOnScreen(image)
    
    def ajustar_coordenadas(self):
        """Verifica a coordenada atual do mouse"""
        st.write("Iniciando em... 2 segundos")
        time.sleep(1)
        st.write("Ajuste o mouse na posição desejada")
        time.sleep(2)
        x, y = pyautogui.position()
        st.write(f"[DEBUG] Coordenadas atuais: ({x}, {y}) capturadas")
        time.sleep(3)
        return x, y

produtos: dict = {
    "nome": "Groudon",
    "preco": 1000,
    "quantidade": 1,
    "descricao": "Pokemon lendário da região de Hoenn",
    "categoria": "Pokemon",
    "marca": "Pokemon",
}

pyautogui.PAUSE = 1.5  # Pausa de 1.5 segundos entre os comandos

def abrir_navegador():
    st.write("Abrindo navegador...")
    pyautogui.press("win")
    pyautogui.write("firefox")
    pyautogui.press("enter")
    time.sleep(2)

def digitar_site():
    st.write("Digitando o site...")
    pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
    pyautogui.press("enter")
    time.sleep(2)  # Espera 2 segundos para o site carregar

def fazer_login():
    st.write("Fazendo login...")
    pyautogui.click(822, 436)  # Clica na barra de endereço
    controller = PyDesktopController()
    controller.write("pythonimpresssionador@gmail.com")
    pyautogui.press("tab")  # Clica na barra de endereço
    controller.write("minhasenhasupersecreta")
    pyautogui.press("tab")  # Clica na barra de endereço
    pyautogui.press("enter")  # Clica na barra de endereço
    time.sleep(2)  # Espera 2 segundos para o site carregar

    st.write("Login realizado com sucesso!")
    return True

def cadastrar_produto():
    st.write("Cadastrando produto...")
    # Aqui você pode implementar a lógica para cadastrar o produto
    time.sleep(2)
    st.write("Produto cadastrado com sucesso!")

# Função principal para executar a automação
def executar_automacao():
    st.write("Iniciando a automação...")
    controller = PyDesktopController()

    # Ajustar coordenadas
    for _ in range(3):
        st.write("Ajuste o mouse na posição desejada")
        time.sleep(2)
        x, y = controller.ajustar_coordenadas()
        st.write(f"Coordenadas ajustadas: ({x}, {y})")
        resposta = st.text_input("Digite 'y' para iniciar a automação.... [Y/N]", key=f"tentativa_{_}")
        
        
        if resposta.lower() == "y":
            st.write("Iniciando a automação")
            break
        else:
            st.write(f"Tentativa {_+1}: Automação cancelada")
    else:
        st.write("Todas as tentativas falharam. Automação cancelada")
        return

    # Executar as etapas da automação
    abrir_navegador()
    digitar_site()
    if fazer_login():
        cadastrar_produto()
        st.write("Automação concluída com sucesso!")
    else:
        st.write("Erro ao fazer login. Automação falhou.")

# Interface do Streamlit
st.title("Automação de Cadastro de Produtos")
st.write("Use esta interface para executar a automação e visualizar os logs em tempo real.")

if st.button("Iniciar Automação"):
    executar_automacao()