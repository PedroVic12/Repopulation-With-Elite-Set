import json
import itertools
import os

def create_combinations_json(input_json_path, output_dir="combinations"):
    """
    Cria todas as combinações únicas de parâmetros a partir de um JSON com dois arrays
    e salva cada combinação como um arquivo JSON separado.

    Args:
        input_json_path (str): Caminho para o arquivo JSON de entrada contendo os arrays.
        output_dir (str): Diretório para salvar os arquivos JSON de saída.
    """
    try:
        # Tenta abrir e carregar o arquivo JSON de entrada
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        # Lida com o erro se o arquivo não for encontrado
        print(f"Erro: Arquivo de entrada não encontrado em {input_json_path}")
        return
    except json.JSONDecodeError:
        # Lida com o erro se o formato JSON for inválido
        print(f"Erro: Formato JSON inválido em {input_json_path}")
        return

    # Extrai os arrays 'dado1' e 'dado2' do JSON
    dado1 = data.get("dado1")
    dado2 = data.get("dado2")

    # Verifica se 'dado1' e 'dado2' são listas válidas
    if not isinstance(dado1, list) or not isinstance(dado2, list):
        print("Erro: 'dado1' e 'dado2' devem ser arrays (listas) no JSON de entrada.")
        return

    # Cria o diretório de saída se ele não existir
    # exist_ok=True evita um erro se o diretório já existir
    os.makedirs(output_dir, exist_ok=True)

    combination_count = 0
    # Gera todas as combinações usando itertools.product
    # itertools.product cria um produto cartesiano (todas as pares possíveis)
    for combo in itertools.product(dado1, dado2):
        # Cria um dicionário para a combinação atual
        combination_data = {
            "dado1_value": combo[0], # O primeiro elemento da tupla combo
            "dado2_value": combo[1]  # O segundo elemento da tupla combo
        }

        # Cria um nome de arquivo único para cada combinação
        # :03d formata o número com zeros à esquerda (ex: 000, 001)
        output_filename = os.path.join(output_dir, f"combination_{combination_count:03d}.json")

        try:
            # Abre o arquivo de saída e salva os dados da combinação
            with open(output_filename, 'w', encoding='utf-8') as outfile:
                json.dump(combination_data, outfile, indent=4) # indent=4 para um JSON formatado e legível
            print(f"Criado: {output_filename}")
            combination_count += 1
        except IOError as e:
            # Lida com erros durante a escrita do arquivo
            print(f"Erro ao escrever o arquivo {output_filename}: {e}")

# --- Exemplo de uso do script ---
if __name__ == "__main__":
    # 1. Cria um arquivo 'input.json' de exemplo para demonstração
    sample_input_data = {
        "dado1": [1, 2, 3],
        "dado2": [0.4, 0.5, 0.6, 0.7]
    }
    input_file_name = "input.json"
    with open(input_file_name, "w", encoding='utf-8') as f:
        json.dump(sample_input_data, f, indent=4)
    print(f"Criado '{input_file_name}' para demonstração.")

    # 2. Executa a função para gerar as combinações
    create_combinations_json(input_file_name)
    print("\nTodas as combinações foram geradas no diretório 'combinations'.")
