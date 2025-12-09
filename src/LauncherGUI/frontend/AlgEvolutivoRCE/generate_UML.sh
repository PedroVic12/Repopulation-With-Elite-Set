#!/bin/bash

# garante que o diretório UML existe
mkdir -p UML

# Instala o pyreverse dentro desse pacote
pip install pylint --break-system-packages

# Instalar o que faz os desenhos (arch linux)
pacman -Sy graphviz 

# roda o pyreverse nos dois arquivos
pyreverse alg_evolutivo_rce.py Setup.py -o dot -p Projeto

# converte o diagrama de classes para PNG e joga em UML/
dot -Tpng classes_Projeto.dot -o UML/classes.png


# se quiser também o de pacotes, descomente a linha abaixo
# dot -Tpng packages_Projeto.dot -o UML/packages.png

# apaga os arquivos .dot gerados

echo "✅ Diagrama gerado em UML/classes.png com sucesso!"
