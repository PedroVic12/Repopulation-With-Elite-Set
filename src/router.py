# src/router.py
import os
import sys
import time

print("Router.py: Iniciando a execução...")
print(f"Router.py: Argumentos recebidos: {sys.argv[1:]}")

# Exemplo: executar um script de teste
# Certifique-se de que 'test_script.py' existe no mesmo diretório ou em um PATH acessível
print("Router.py: Chamando test_script.py via os.system()...")
# Usamos sys.executable para garantir que o mesmo interpretador Python seja usado
os.system(f"{sys.executable} {os.path.join(os.path.dirname(__file__), 'test_script.py')}")

print("Router.py: Chamada a test_script.py concluída.")
print("Router.py: Executando outro comando de sistema (ls -l)...")
os.system("ls -l") # Exemplo de outro comando de sistema

print("Router.py: Finalizando execução.")