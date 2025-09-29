import pyautogui
import time

class PyDesktopController:
    def __init__(self):
        pass

    def click(self, x, y):
        """"Clica na posição (x, y) da tela"""
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
        print("iniciando em... 2 segundos")
        time.sleep(1)
        print("Ajuste o mouse na posição desejada")
        time.sleep(2)
        x, y = pyautogui.position()
        print(f"[DEBUG] Coordenadas atuais: ({x}, {y}) capturadas")
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
    pyautogui.press("win")
    pyautogui.write("firefox")
    pyautogui.press("enter")
    time.sleep(2)

def digitar_site():
    url_test = "http://localhost:8501"
    #pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
    pyautogui.write(url_test)
    pyautogui.press("enter")
    time.sleep(2)  # Espera 5 segundos para o site carregar

def fazer_login():
    pyautogui.click(822, 436) # Clica na barra de endereço
    controller = PyDesktopController()
    controller.write("pythonimpresssionador@gmail.com")
    pyautogui.press("tab")  # Clica na barra de endereço
    controller.write("minhasenhasupersecreta")
    pyautogui.press("tab")  # Clica na barra de endereço
    pyautogui.press("enter")  # Clica na barra de endereço
    time.sleep(2)  # Espera 5 segundos para o site carregar

    test = True

    if test:
        return True
    else:
        print("Erro ao fazer login")
        return False

        
def cadastrar_produto():
    pyautogui.click(536, 377) # Clica na barra de endereço
    controller = PyDesktopController()
    controller.write("produto teste")
    pyautogui.press("tab")
    controller.write("marca")
    pyautogui.press("tab")
    controller.write("tipo")
    pyautogui.press("tab")
    controller.write("categoria")
    pyautogui.press("tab")
    pyautogui.write("preco unitario")
    pyautogui.press("tab")
    pyautogui.write("custo")
    pyautogui.press("tab")

    # scroll suave
    pyautogui.press("tab")
    controller.press("observaçoes de pedro victor...")
    pyautogui.press("tab")
    pyautogui.press("enter")


if __name__ == "__main__":
    print("Iniciando o cadastro do produto")
    automateSucess = False
    controller = PyDesktopController()
    for _ in range(3):
        print("Ajuste o mouse na posição desejada")
        time.sleep(2)
        controller.ajustar_coordenadas()
        print("Coordenadas do mouse:")
        time.sleep(1)
        resposta = input("Digite 'y' para iniciar a automação.... [Y/N]")
        if resposta.lower() == "y":
            print("Iniciando a automação")
            break
        else:
            print("Tentativa", _+1, " Automação cancelada")
    else:
        print("Todas as tentativas falharam. Automação cancelada")
        exit()
    
    abrir_navegador()
    digitar_site()
    fazer_login()
    cadastrar_produto()

    if automateSucess:
        print("Automação concluída com sucesso")
    else:
        print("Automação falhou")
    
    
    print("\n\nFim!")
