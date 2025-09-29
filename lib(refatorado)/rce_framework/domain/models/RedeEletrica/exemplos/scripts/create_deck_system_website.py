import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


#projeto ciencia de dados


# projeto de modelagem em pandapower

# pipeline de addos para criar um website com entrada de dados de execel do SIN
nome_aba = ["R_REDESPACHO", "C_Controle_de_Casos", "DBSH","C_Mapa"]
path_planilha = r"C:\Users\pedrovictor.veras\OneDrive - Operador Nacional do Sistema Eletrico\Documentos\ESTAGIO ONS PVRV 2025\GitHub\Electrical-System-Simulator\backend\database\FLOW_ONS_geracao_despacho_SIN.xlsm"
SIN_df = pd.read_excel(path_planilha,
                       sheet_name=nome_aba[0],  skiprows=5, engine='openpyxl')

BARRAS_SHUNT_DF = pd.read_excel(path_planilha,
                                sheet_name=nome_aba[2], skiprows=6, engine='openpyxl')

# função para limpar a tabela e exportar o dataset limpo
def clean_table(df, output_path = "output_dataset.xlsx", debug = False):

    # Dados da minha tabela
    if debug:
        print("Colunas do DataFrame:")
        print(df.columns)
        print("Número de linhas:", len(df))
        


    # fatiamento do dataframe
    df = df.iloc[:, 0:33]  # Seleciona as primeiras 33 colunas
    #SIN_df = SIN_df.dropna(axis=0, how='all')  # Remove linhas que estão completamente vazias

    # Exibir as primeiras linhas do DataFrame
    print(df.head())

    #exporta o dataset do SIN
    df.to_excel(
        "./SIN_dataset.xlsx",
        index=False,
        sheet_name="Usinas",
        engine='openpyxl'
    )

def plot_barras(df, column_name):
    """
    Plota um gráfico de barras para a coluna especificada do DataFrame.
    """
    plt.figure(figsize=(10, 6))
    df[column_name].value_counts().plot(kind='bar')
    plt.title(f'Contagem de {column_name}')
    plt.xlabel(column_name)
    plt.ylabel('Contagem')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Limpa a tabela e exporta o dataset
    clean_table(SIN_df)

    # Exemplo de uso da função de plotagem
    #plot_barras(SIN_df, 'Nome da Usina')  # Exemplo de plotagem para uma coluna específica

    # todo
    # filtrar as barras shunt 
    # 1) tensão = 500kv
    # 2) manobra = S
    # 3) unidade de operação = 1 e tenho que alterar para 0
    # 4) analisar as tensões de operação de V em pu para ver se esta limitando os limites
    clean_table(BARRAS_SHUNT_DF, output_path="./BARRAS_SHUNT_dataset.xlsx", debug=True)

    # Exemplo de uso da função de plotagem
    plot_barras(BARRAS_SHUNT_DF, 'V (pu)')  # Exemplo de plotagem para a coluna 'V (pu)'