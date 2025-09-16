# -*- coding: utf-8 -*-
"""
Arquivo: inspect_excel_data.py

Objetivo: Inspecionar o arquivo SIN_45_barras_dataset.xlsx e criar os DataFrames
de agendamento e contingência a partir dos dados lidos.
"""

import os
import pandas as pd

class SmartGridSin45:
    """
    Classe para gerenciar os dados e a criação da rede elétrica do sistema SIN 45 Barras.
    """
    def create_sin45_dataset_file(self, filename='SIN_45_barras_dataset.xlsx'):
        """
        Cria um arquivo Excel com os dados do sistema SIN 45 Barras.
        """
        # Dicionários com os dados do SIN 45 Barras
        nomes_barras = {'Barra': list(range(1, 46)),'Nome': ['IVAIPORA.525', 'LONDRINA.525', 'BARRACAO13.8', 'SIDEROPOL230', 'FARROUPIL230','P.FUNDO.13.8', 'P.FUNDO.230', 'XANXERE.230', 'P.BRANCO.230', 'S.OSORIO13.8','S.OSORIO.230', 'AREIA.230', 'S.MATEUS.230', 'CURITIBA.230', 'JOINVILE.230','BLUMENAU.230', 'R.QUEIMAD230', 'F.AREIA.13.8', 'AREIA.525', 'CURITIBA.525','CUR.NORTE525', 'BLUMENAU.525', 'BARRACAO.525', 'GRAVATAI.525', 'V.AIRES.525','PINHEIRO.525', 'S.SANTIA13.8', 'S.SANTIAG525', 'J.LAC.A.13.8', 'J.LACERDA138','J.LAC.B.13.8', 'J.LAC.C.13.8', 'J.LACERDA230', 'SEGREDO.13.8', 'SEGREDO.525','CECI.230', 'GRAVATAI.230', 'ITAUBA.13.8', 'ITAUBA.230', 'V.AIRES.230','APUCARANA230', 'LONDRINA.230', 'MARINGA.230', 'C.MOURAO.230', 'FORQUILHI230']}
        reatores = {'Barra': [1, 20, 21, 23, 24, 25],'Susceptância Shunt B(pu)': [-2.000, -1.500, -1.500, -1.000, -1.500, -1.500]}
        dados_rede = {'De': [1, 1, 1, 2, 3, 4, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 10, 11, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 19, 19, 19, 19, 20, 20, 23, 24, 25, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 36, 38, 39, 41, 41, 41, 42, 43],'Para': [2, 19, 28, 42, 23, 5, 33, 45, 7, 36, 7, 8, 39, 9, 11, 11, 11, 12, 44, 13, 19, 14, 15, 20, 16, 17, 22, 33, 19, 20, 21, 23, 35, 21, 22, 24, 37, 26, 40, 28, 28, 35, 30, 33, 33, 33, 45, 35, 37, 40, 39, 40, 42, 43, 44, 43, 44],'R(pu)': [0.00035, 0.0018, 0.0014, 0.0, 0.0, 0.0386, 0.0096, 0.0033, 0.02315, 0.00885, 0.0, 0.00815, 0.025, 0.0163, 0.0316, 0.0153, 0.0, 0.0306, 0.0172, 0.0245, 0.0, 0.0088, 0.0091, 0.0, 0.0077, 0.0108, 0.0, 0.009, 0.0, 0.0019, 0.0019, 0.0014, 0.0005, 0.0005, 0.0012, 0.0021, 0.0, 0.0022, 0.0, 0.0014, 0.0, 0.0005, 0.0, 0.0, 0.0, 0.0129, 0.0, 0.0006971, 0.0061315, 0.0, 0.0202, 0.0051987, 0.011, 0.0229, 0.0086, 0.0181],'X(pu)': [0.00725, 0.0227, 0.0204, 0.0063, 0.0136, 0.1985, 0.0491, 0.0167, 0.1189, 0.0455, 0.046, 0.04175, 0.1548, 0.0835, 0.1621, 0.0861, 0.0114, 0.1523, 0.088, 0.1256, 0.03, 0.0415, 0.04675, 0.0062, 0.0388, 0.05525, 0.0062, 0.046, 0.0067, 0.028, 0.0274, 0.0195, 0.007, 0.0069, 0.0175, 0.0309, 0.0062, 0.03, 0.0062, 0.0195, 0.0114, 0.007, 0.0871, 0.059, 0.0701, 0.045, 0.0657, 0.0068, 0.0035819, 0.0316242, 0.0236, 0.1129, 0.0268149, 0.1184, 0.1174, 0.0442, 0.0929],'B(pu)': [0.8305, 2.2721, 2.4475, 0.0, 0.0, 0.34, 0.0842, 0.2859, 0.2042, 0.07925, 0.0, 0.072, 0.469, 0.144, 0.2784, 0.1344, 0.0, 0.2702, 0.152, 0.2041, 0.0, 0.5211, 0.07975, 0.0, 0.0675, 0.09315, 0.0, 0.07765, 0.0, 3.3576, 3.2867, 2.3968, 0.8392, 0.8216, 2.097, 3.7183, 0.0, 3.83, 0.0, 2.397, 0.0, 0.8392, 0.0, 0.0, 0.0, 0.0, 0.1128, 0.0, 0.0668, 0.5236, 0.0, 0.2062, 0.1905, 0.2027, 0.2027, 0.2868, 0.1607]}
        dados_rede = {'De': [1, 1, 1, 2, 3, 4, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 10, 11, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 19, 19, 19, 19, 20, 20, 23, 24, 25, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 36, 38, 39, 41, 41, 41, 42, 43],'Para': [2, 19, 28, 42, 23, 5, 33, 45, 7, 36, 7, 8, 39, 9, 11, 11, 11, 12, 44, 13, 19, 14, 15, 20, 16, 17, 22, 33, 19, 20, 21, 23, 35, 21, 22, 24, 37, 26, 40, 28, 28, 35, 30, 33, 33, 33, 45, 35, 37, 40, 39, 40, 42, 43, 44, 43, 44],'R(pu)': [0.00035, 0.0018, 0.0014, 0.0, 0.0, 0.0386, 0.0096, 0.0033, 0.02315, 0.00885, 0.0, 0.00815, 0.025, 0.0163, 0.0316, 0.0153, 0.0, 0.0306, 0.0172, 0.0245, 0.0, 0.0088, 0.0091, 0.0, 0.0077, 0.0108, 0.0, 0.009, 0.0, 0.0019, 0.0019, 0.0014, 0.0005, 0.0005, 0.0012, 0.0021, 0.0, 0.0022, 0.0, 0.0014, 0.0, 0.0005, 0.0, 0.0, 0.0, 0.0129, 0.0, 0.0006971, 0.0061315, 0.0, 0.0202, 0.0051987, 0.011, 0.0229, 0.0086, 0.0181],'X(pu)': [0.00725, 0.0227, 0.0204, 0.0063, 0.0136, 0.1985, 0.0491, 0.0167, 0.1189, 0.0455, 0.046, 0.04175, 0.1548, 0.0835, 0.1621, 0.0861, 0.0114, 0.1523, 0.088, 0.1256, 0.03, 0.0415, 0.04675, 0.0062, 0.0388, 0.05525, 0.0062, 0.046, 0.0067, 0.028, 0.0274, 0.0195, 0.007, 0.0069, 0.0175, 0.0309, 0.0062, 0.03, 0.0062, 0.0195, 0.0114, 0.007, 0.0871, 0.059, 0.0701, 0.045, 0.0657, 0.0068, 0.0035819, 0.0316242, 0.0236, 0.1129, 0.0268149, 0.1184, 0.1174, 0.0442, 0.0929],'B(pu)': [0.8305, 2.2721, 2.4475, 0.0, 0.0, 0.34, 0.0842, 0.2859, 0.2042, 0.07925, 0.0, 0.072, 0.469, 0.144, 0.2784, 0.1344, 0.0, 0.2702, 0.152, 0.2041, 0.0, 0.5211, 0.07975, 0.0, 0.0675, 0.09315, 0.0, 0.07765, 0.0, 3.3576, 3.2867, 2.3968, 0.8392, 0.8216, 2.097, 3.7183, 0.0, 3.83, 0.0, 2.397, 0.0, 0.8392, 0.0, 0.0, 0.0, 0.0, 0.1128, 0.0, 0.0668, 0.5236, 0.0, 0.2062, 0.1905, 0.2027, 0.2027, 0.2868, 0.1607]}
        carga_leve = {'Barra': list(range(1, 46)),'Tipo de Barra (*)': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],'Potência Ativa (MW)': [0.0, 0.0, 1000.0, 0.0, 0.0, 172.0, 0.0, 0.0, 0.0, 736.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1248.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1060.0, 0.0, 72.0, 0.0, 96.0, 192.8, 0.0, 1060.8, 0.0, 0.0, 0.0, 392.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],'Carga Ativa (MW)': [720.1334, 0.0, 0.0, 141.6, 153.0934, 0.0, 136.8, 100.8, 37.2534, 0.0, 224.8, 223.7067, 104.16, 342.36, 248.3734, 339.4934, 94.24, 0.0, 0.0, 0.0, 294.4, 0.0, 139.656, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.832, 0.0, 0.0, 0.0, 0.0, 0.0, 650.4, 489.6, 0.0, 323.2, 314.4, 209.6, 183.2, 147.2, 111.2, 72.08],'Carga Reativa (Mvar)': [0.0, 0.0, 0.0, 54.4, 33.6, 0.0, 14.8, 37.6, 11.76, 0.0, 45.2, 48.56, 23.52, -20.0, 112.8, 72.48, 42.48, 0.0, 0.0, 0.0, 55.68, 0.0, -6.56, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 31.84, 0.0, 0.0, 0.0, 0.0, 0.0, 88.0, -364.0, 0.0, 108.0, -88.8, 10.56, 146.4, 48.16, 42.96, 44.24]}
        
        filepath = os.path.join(os.getcwd(), filename)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            pd.DataFrame(nomes_barras).to_excel(writer, sheet_name='bus', index=False)
            pd.DataFrame(dados_rede).to_excel(writer, sheet_name='line', index=False)
            pd.DataFrame(carga_leve).to_excel(writer, sheet_name='load_gen', index=False)
            pd.DataFrame(reatores).to_excel(writer, sheet_name='shunt', index=False)
        return filepath


if __name__ == '__main__':
    excel_file = 'SIN_45_barras_dataset.xlsx'

    if not os.path.exists(excel_file):
        print(f"Arquivo {excel_file} não encontrado. Criando o arquivo...")
        smart_grid = SmartGridSin45()
        smart_grid.create_sin45_dataset_file(excel_file)
        print("Arquivo criado com sucesso.")

    try:
        xls = pd.ExcelFile(excel_file)
        print(f"Inspecionando o arquivo: {excel_file}")
        for sheet_name in xls.sheet_names:
            print(f"\n--- Folha: {sheet_name} ---")
            df = pd.read_excel(xls, sheet_name)
            print(df.head())

        df_line = pd.read_excel(xls, 'line')

        agendamento_df = pd.DataFrame({
            'ramo': df_line[['De', 'Para']].head(5).values.tolist(),
            'duracao': [5, 4, 6, 3, 5],
            'prioridade': [1, 2, 1, 3, 1]
        })
        print("\n--- agendamento_df criado a partir do Excel ---")
        print(agendamento_df)

        contingencia_df = pd.DataFrame({
            'contingencia': range(1, 4),
            'from': df_line['De'].iloc[5:8].values,
            'to': df_line['Para'].iloc[5:8].values
        })
        print("\n--- contingencia_df criado a partir do Excel ---")
        print(contingencia_df)

    except FileNotFoundError:
        print(f"Erro: O arquivo {excel_file} não foi encontrado e não pôde ser criado.")
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
