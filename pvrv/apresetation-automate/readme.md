# 🎯 Sistema de Apresentação Controlado por Gestos

Sistema completo para apresentar slides (PDF/PowerPoint) usando gestos das mãos detectados por câmera, desenvolvido com Python, OpenCV e MediaPipe.

## 🚀 Funcionalidades

* ✅ Converte PDF e PowerPoint em imagens de alta qualidade
* 👋 Controle por gestos usando MediaPipe
* 📹 Visualização em tempo real da câmera
* 🎨 Interface em tela cheia profissional
* ⚡ Programação funcional e modular


1. **converter.py** - Converte PDF/PowerPoint em imagens de alta qualidade
2. **gesture_detector.py** - Detecta gestos das mãos em tempo real
3. **presenter.py** - Apresentador principal com interface em tela cheia
4. **main.py** - Script principal que integra tudo
5. **test_camera.py** - Script de teste para verificar câmera e MediaPipe
6. **README.md** - Documentação completa
7. **.gitignore** - Configuração Git

## 🎮 Gestos implementados:

* **👉 Mão direita** deslizando para  **esquerda** : Próximo slide
* **👈 Mão esquerda** deslizando para  **direita** : Slide anterior
* **✌️ Sinal de paz** (2 dedos): Fechar apresentação
* **ESC/Q** : Sair

## 🚀 Como usar:

bash

```bash
# 1. Configurar projeto
bash setup_project.sh

# 2. Testar câmera e MediaPipe (recomendado)
uv run python test_camera.py

# 3. Colocar PDF/PPT na pasta input/
cp sua_apresentacao.pdf input/

# 4. Executar
uv run python main.py
```

## ✨ Características técnicas:

* **Programação funcional e modular**
* Alta qualidade (300 DPI padrão, configurável)
* Detecção robusta com histórico de posições
* Cooldown de 1s entre gestos
* Miniatura da câmera no canto
* Suporte a Python 3.10-3.12

## 📋 Requisitos

* Python 3.10, 3.11 ou 3.12 (MediaPipe não suporta 3.13+)
* Webcam
* UV (gerenciador de pacotes)

## 🔧 Instalação

### 1. Clone ou crie o projeto

```bash
# Executar script de setup
bash setup_project.sh
```

### 2. Instalação manual (alternativa)

```bash
# Criar ambiente
mkdir gesture-presentation && cd gesture-presentation
mkdir -p apresentacao-imgs input

# Instalar UV (se necessário)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências
uv pip install opencv-python mediapipe PyMuPDF pillow python-pptx
```

## 📖 Como Usar

### Opção 1: Conversão automática

```bash
# Coloque seu PDF/PPT na pasta input/
cp sua_apresentacao.pdf input/

# Execute
uv run python main.py
```

### Opção 2: Arquivo específico

```bash
uv run python main.py --input /caminho/para/apresentacao.pdf
```

### Opção 3: Usar imagens já convertidas

```bash
# Se já converteu anteriormente
uv run python main.py --skip-convert
```

## 🎮 Gestos Suportados

| Gesto                                             | Ação                |
| ------------------------------------------------- | --------------------- |
| 👉**Mão direita deslizando para esquerda** | Próximo slide        |
| 👈**Mão esquerda deslizando para direita** | Slide anterior        |
| ✌️**Sinal de paz (2 dedos)**              | Fechar apresentação |
| ESC / Q                                           | Sair                  |

### 💡 Dicas para Melhor Detecção

1. **Iluminação** : Use ambiente bem iluminado
2. **Distância** : Fique a 50cm-1m da câmera
3. **Fundo** : Prefira fundos neutros
4. **Velocidade** : Faça gestos de swipe com movimento rápido e contínuo
5. **Pausa** : Aguarde 1 segundo entre gestos

## 📁 Estrutura do Projeto

```
gesture-presentation/
├── main.py              # Script principal
├── converter.py         # Conversão PDF/PPT → Imagens
├── gesture_detector.py  # Detecção de gestos
├── presenter.py         # Apresentador de slides
├── pyproject.toml       # Configuração UV
├── input/               # Coloque arquivos aqui
└── apresentacao-imgs/   # Imagens geradas
```

## 🎨 Opções Avançadas

### Alterar resolução DPI

```bash
uv run python main.py --dpi 450  # Maior qualidade
```

### Diretório de saída customizado

```bash
uv run python main.py --output-dir minhas-imgs
```

### Ver todas as opções

```bash
uv run python main.py --help
```

## 🐛 Troubleshooting

### Erro: "MediaPipe requires Python < 3.13"

```bash
# Instale Python 3.12
pyenv install 3.12.0
pyenv local 3.12.0
```

### Câmera não detectada

```bash
# Teste a câmera
python -c "import cv2; print('OK' if cv2.VideoCapture(0).isOpened() else 'ERRO')"
```

### Gestos não detectados

* Verifique iluminação
* Certifique-se que a mão está visível
* Aumente `min_detection_confidence` em `gesture_detector.py`

### PowerPoint não converte bem

⚠️  **Recomendação** : Exporte o PPT como PDF primeiro para melhor qualidade.

No PowerPoint: `Arquivo → Exportar → Criar PDF/XPS`

## 🔬 Arquitetura Técnica

### Módulos

 **converter.py** : Programação funcional para conversão

* `pdf_to_images()`: Usa PyMuPDF com alta resolução
* `pptx_to_images()`: Processa slides do PowerPoint
* `convert_presentation()`: Interface unificada

 **gesture_detector.py** : Detecção em tempo real

* `GestureDetector`: Classe para processar frames
* `count_fingers()`: Conta dedos levantados
* `detect_swipe()`: Detecta movimentos de deslize
* Histórico de posições para tracking

 **presenter.py** : Renderização e controle

* `GesturePresenter`: Gerencia apresentação
* Miniatura da câmera no canto
* Navegação por gestos e teclado
* Interface em tela cheia

## 📊 Fluxo de Dados

```
PDF/PPTX → [converter.py] → Imagens PNG
    ↓
Imagens → [presenter.py] → Renderização
    ↓
Câmera → [gesture_detector.py] → Gestos
    ↓
Gestos → [presenter.py] → Ações
```

## 🎓 Para Estudantes de Engenharia

Este projeto integra conceitos de:

* **Visão Computacional** : OpenCV, processamento de imagens
* **Machine Learning** : MediaPipe para detecção de mãos
* **Processamento de Sinais** : Análise de movimento temporal
* **Engenharia de Software** : Programação funcional, modular
* **Interface Humano-Computador** : Gestos naturais

## 📝 Licença

MIT License - Livre para uso acadêmico e comercial

## 🤝 Contribuições

PRs são bem-vindos! Áreas para melhoria:

* [ ] Mais gestos (zoom, anotações)
* [ ] Suporte a vídeos nos slides
* [ ] Gravação da apresentação
* [ ] Interface de configuração
* [ ] Suporte a múltiplos monitores

## 📧 Suporte

Encontrou algum problema? Abra uma issue!

---

**Desenvolvido com ❤️ usando Python, OpenCV e MediaPipe**
