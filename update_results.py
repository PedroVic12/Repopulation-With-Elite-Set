import pandas as pd
import json
from pathlib import Path

def update_consolidated_results():
    BASE_DIR = Path(__file__).parent
    SRC_DIR = BASE_DIR / "src"
    OUTPUT_DIR = SRC_DIR / "output"
    RESULTS_FILE = OUTPUT_DIR / "results_consolidados.xlsx"

    if not RESULTS_FILE.exists():
        print(f"Arquivo {RESULTS_FILE} não encontrado.")
        return

    try:
        df = pd.read_excel(RESULTS_FILE)
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return

    # Dicionário para armazenar os parâmetros de cada configuração
    config_params = {}

    # Itera sobre os arquivos de configuração para extrair os parâmetros
    for config_file in sorted(OUTPUT_DIR.glob("params_config*.json")):
        try:
            config_num = int(config_file.stem.split('_')[-1])
            with open(config_file, 'r') as f:
                params = json.load(f)
                config_params[config_num] = {
                    "MUTACAO": params.get("MUTACAO"),
                    "CROSSOVER": params.get("CROSSOVER"),
                    "NUM_GENERATIONS": params.get("NUM_GENERATIONS"),
                    "POP_SIZE": params.get("POP_SIZE"),
                }
        except (ValueError, IndexError, json.JSONDecodeError) as e:
            print(f"Erro ao processar o arquivo {config_file.name}: {e}")
            continue

    # Adiciona as novas colunas ao DataFrame
    df['Config_Num'] = df['Execucao'].apply(lambda x: int(x.split('_')[0]))
    df['MUTACAO'] = df['Config_Num'].apply(lambda x: config_params.get(x, {}).get('MUTACAO'))
    df['CROSSOVER'] = df['Config_Num'].apply(lambda x: config_params.get(x, {}).get('CROSSOVER'))
    df['NUM_GENERATIONS'] = df['Config_Num'].apply(lambda x: config_params.get(x, {}).get('NUM_GENERATIONS'))
    df['POP_SIZE'] = df['Config_Num'].apply(lambda x: config_params.get(x, {}).get('POP_SIZE'))

    try:
        df.to_excel(RESULTS_FILE, index=False)
        print(f"Arquivo {RESULTS_FILE} atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar o arquivo Excel: {e}")

if __name__ == "__main__":
    update_consolidated_results()
