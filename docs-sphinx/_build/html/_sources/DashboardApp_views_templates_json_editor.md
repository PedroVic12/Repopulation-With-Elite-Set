# json_editor.py

```python
import streamlit as st
import json
import os
from datetime import datetime
from PIL import ImageGrab

# Função para carregar o arquivo JSON
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        st.error(f"Arquivo {file_path} não encontrado!")
        return {}

# Função para salvar o arquivo JSON
def save_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    st.success(f"Arquivo salvo com sucesso em: {file_path}")

# Função para tirar um screenshot da tela
def save_screenshot(output_path):
    screenshot = ImageGrab.grab()
    screenshot.save(output_path)
    st.success(f"Screenshot salvo em: {output_path}")

# Caminho do arquivo JSON
json_file_path = "parameters.json"

# Carregar o JSON
st.title("Editor de JSON em Tempo Real")
st.subheader("Carregue, edite e salve seu arquivo JSON diretamente nesta interface.")

# Carregar o JSON inicial
params = load_json(json_file_path)

# Exibir o JSON em um editor
st.write("### JSON Atual")
edited_json = st.json(params, expanded=True)

# Botão para salvar o JSON editado
if st.button("Salvar JSON"):
    save_json(json_file_path, edited_json)

# Botão para tirar um screenshot da tela
if st.button("Salvar Screenshot"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshot_{timestamp}.png"
    save_screenshot(screenshot_path)

# Exibir mensagem de instrução
st.info("Edite os valores no editor acima e clique em 'Salvar JSON' para salvar as alterações no arquivo.")
```