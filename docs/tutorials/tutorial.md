# Tutorial de Uso do Framework RCE Otimizado

Este tutorial fornece um guia passo a passo sobre como configurar e executar o framework de otimização `Repopulation-With-Elite-Set` (RCE).

---

## 1. Estrutura do Projeto

A estrutura principal do projeto foi organizada da seguinte forma:

- **`lib/rce_framework/`**: Contém o núcleo do algoritmo, incluindo a lógica de setup, o algoritmo evolutivo e as funções de fitness.
- **`src/`**: Contém os arquivos de configuração (`params.json`, `options.json`), o `laucher.py` (interface gráfica) e o `DashboardApp/` (visualização de resultados).
- **`test/`**: Contém os testes unitários para garantir a integridade do framework.
- **`output/`**: Diretório onde todos os resultados das execuções (gráficos, logs e planilhas) são salvos.

---

## 2. Configuração do Ambiente

Antes de executar o framework, certifique-se de que todos os pré-requisitos estão instalados.

### Pré-requisitos
- Python 3.8 ou superior

### Instalação das Dependências

Para instalar todas as bibliotecas necessárias, execute o seguinte comando no terminal, a partir da raiz do projeto:

```bash
pip install -r requirements.txt
```

--- 

## 3. Executando o Framework

Existem duas maneiras principais de executar o framework:

### Método 1: Usando o Launcher Gráfico (Recomendado)

O `laucher.py` fornece uma interface gráfica amigável para configurar e executar os experimentos.

1.  **Abra o terminal** na raiz do projeto.
2.  **Execute o launcher** com o seguinte comando:

    ```bash
    python laucher.py
    ```

3.  **Na aba "⚙️ Configuração e Execução"**:
    - Defina o número de execuções por configuração.
    - Ajuste os parâmetros do algoritmo genético (Mutação, Crossover, etc.) usando os modos "Fixo" ou "Variável".
    - Clique em **"💾 Salvar e Executar"**.

4.  **Acompanhe a execução** na aba **"📊 Dashboard e Logs"**.

### Método 2: Execução Direta via Script

Para usuários avançados, é possível executar o framework diretamente.

1.  **Configure os parâmetros** nos arquivos `src/params.json` (parâmetros base) e `src/options.json` (parâmetros variáveis e de execução).
2.  **Execute o script principal** a partir da raiz do projeto:

    ```bash
    python lib/rce_framework/main.py
    ```

--- 

## 4. Visualizando os Resultados

Após a execução, os resultados são salvos na pasta `output/`. Para uma visualização interativa, use o Dashboard Streamlit.

1.  **Navegue até a pasta do Dashboard**:

    ```bash
    cd src/DashboardApp
    ```

2.  **Inicie o aplicativo Streamlit**:

    ```bash
    streamlit run dashboard_RCE_APP.py
    ```

3.  **Acesse o dashboard** no seu navegador, geralmente no endereço `http://localhost:8501`.

---

## 5. Exemplo Básico de Uso do Pandapower

Para entender a base da simulação de redes elétricas utilizada no framework, você pode executar o script `quick_start.py`.

```bash
python quick_start.py
```

Este script demonstra como criar uma rede simples, executar um fluxo de potência e exibir os resultados, ilustrando os conceitos fundamentais do `pandapower`.