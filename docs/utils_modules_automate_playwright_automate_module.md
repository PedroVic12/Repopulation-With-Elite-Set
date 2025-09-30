# playwright_automate_module.py

```python
from playwright.sync_api import sync_playwright
import time

#https://www.youtube.com/watch?v=4kPRm8D8Vx0&list=PLpdAy0tYrnKyjrY1Fr72DhmrRmeWI_5C8&index=36



def go_to_website(page, url):
    page.goto(url)

def click_element(page, xpath):
    page.locator(xpath).click()

def fill_input(page, xpath, value):
    page.fill(xpath, value)

def wait_for_page_load(seconds):
    time.sleep(seconds)

def close_browser(browser):
    browser.close()

def main():
    url = "https://www.hashtagtreinamentos.com/curso-python"  # Replace with the actual URL

    # Gerenciar o ciclo de vida do navegador e da página
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navegar para o site
            go_to_website(page, url)
            wait_for_page_load(5)  # Aguarde 5 segundos para carregar a página

            xpath_nome = 'xpath=//*[@id="firstname"]'  # Replace with the actual XPath
            xpath_to_email = 'xpath=//*[@id="email"]'  # Replace with the actual XPath
            xpath_to_phone = 'xpath=//*[@id="phone"]'  # Replace with the actual XPath
            xpath_botao = 'xpath=//*[@id="_form_2475_submit"]'

            # Preenchendo campos
            fill_input(page, xpath_nome, "Pedro Victor")
            click_element(page, xpath_nome)

            fill_input(page, xpath_to_email, "admin@gmail.com")
            fill_input(page, xpath_to_phone, "2199999999")

            click_element(page, xpath_botao)
            wait_for_page_load(9)  # Aguarde 5 segundos para carregar a página



        except Exception as e:
            print(f"Erro durante a execução: {e}")
        finally:
            # Fechar o navegador
            print("Fechando o navegador...")
            browser.close()

if __name__ == "__main__":
    main()
```