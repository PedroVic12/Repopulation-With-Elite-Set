import pandas as pd
import argparse
import sys
from pathlib import Path

def verify_dataset(file_path: Path):
    """Lê um arquivo Excel e imprime as primeiras 5 linhas (head)."""
    try:
        print(f"--- Verificando arquivo: {file_path.resolve()} ---")
        
        if not file_path.exists():
            print(f"\n❌ ERRO: O arquivo não foi encontrado no caminho especificado.")
            return

        # Lê o arquivo Excel
        df = pd.read_excel(file_path)
        
        print("\n✅ Arquivo lido com sucesso!")
        print("\n--- Primeiras 5 linhas (head) do dataset: ---")
        print(df.head())
        
        print("\n--- Informações do DataFrame (colunas, tipos, etc.): ---")
        df.info()

    except FileNotFoundError:
        print(f"\n❌ ERRO: Arquivo não encontrado. Verifique o caminho.")
    except Exception as e:
        print(f"\n❌ ERRO: Ocorreu um erro ao ler o arquivo: {e}")
        print("Verifique se o arquivo é um .xlsx válido e se o pandas e openpyxl estão instalados.")

def main():
    """Função principal para executar o script via linha de comando."""
    parser = argparse.ArgumentParser(
        description="Verifica as primeiras linhas de um arquivo Excel.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'path',
        type=str,
        help='Caminho para o arquivo .xlsx a ser verificado.\nExemplo: python verificar_dataset.py src/output/resultados.xlsx'
    )
    
    args = parser.parse_args()
    
    # Converte o caminho para um objeto Path
    file_path = Path(args.path)
    
    verify_dataset(file_path)

if __name__ == "__main__":
    main()
