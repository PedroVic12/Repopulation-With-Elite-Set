# -*- coding: utf-8 -*-
import os
import pandas as pd

class SmartGridSin45:
    """
    Classe para criar o dataset do sistema SIN 45 Barras.
    """
    def create_sin45_dataset_file(self, filename='SIN_45_barras_dataset.xlsx'):
        nomes_barras = {'Barra': list(range(1, 46)),
                        'Nome': ['IVAIPORA.525', 'LONDRINA.525', 'BARRACAO13.8', 'SIDEROPOL230',
                                 'FARROUPIL230','P.FUNDO.13.8', 'P.FUNDO.230', 'XANXERE.230',
                                 'P.BRANCO.230', 'S.OSORIO13.8','S.OSORIO.230', 'AREIA.230',
                                 'S.MATEUS.230', 'CURITIBA.230', 'JOINVILE.230','BLUMENAU.230',
                                 'R.QUEIMAD230', 'F.AREIA.13.8', 'AREIA.525', 'CURITIBA.525',
                                 'CUR.NORTE525', 'BLUMENAU.525', 'BARRACAO.525', 'GRAVATAI.525',
                                 'V.AIRES.525','PINHEIRO.525', 'S.SANTIA13.8', 'S.SANTIAG525',
                                 'J.LAC.A.13.8', 'J.LACERDA138','J.LAC.B.13.8', 'J.LAC.C.13.8',
                                 'J.LACERDA230', 'SEGREDO.13.8', 'SEGREDO.525','CECI.230',
                                 'GRAVATAI.230', 'ITAUBA.13.8', 'ITAUBA.230', 'V.AIRES.230',
                                 'APUCARANA230', 'LONDRINA.230', 'MARINGA.230', 'C.MOURAO.230',
                                 'FORQUILHI230']}
        reatores = {'Barra': [1, 20, 21, 23, 24, 25],
                    'Susceptância Shunt B(pu)': [-2.000, -1.500, -1.500, -1.000, -1.500, -1.500]}
        dados_rede = {
            'De': [1, 1, 1, 2, 3], 'Para': [2, 19, 28, 42, 23],
            'R(pu)': [0.00035, 0.0018, 0.0014, 0.0, 0.0],
            'X(pu)': [0.00725, 0.0227, 0.0204, 0.0063, 0.0136],
            'B(pu)': [0.8305, 2.2721, 2.4475, 0.0, 0.0]
        }
        carga_leve = {'Barra': list(range(1, 6)),
                      'Tipo de Barra (*)': [0, 0, 1, 0, 0],
                      'Potência Ativa (MW)': [0.0, 0.0, 1000.0, 0.0, 0.0],
                      'Carga Ativa (MW)': [720.1334, 0.0, 0.0, 141.6, 153.0934],
                      'Carga Reativa (Mvar)': [0.0, 0.0, 0.0, 54.4, 33.6]}

        filepath = os.path.join(os.getcwd(), filename)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            pd.DataFrame(nomes_barras).to_excel(writer, sheet_name='bus', index=False)
            pd.DataFrame(dados_rede).to_excel(writer, sheet_name='line', index=False)
            pd.DataFrame(carga_leve).to_excel(writer, sheet_name='load_gen', index=False)
            pd.DataFrame(reatores).to_excel(writer, sheet_name='shunt', index=False)
        return filepath


class AnaliseExploratoriaDados:
    """
    Classe genérica para análise exploratória de datasets Excel.
    """
    def __init__(self, excel_file: str):
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Arquivo {excel_file} não encontrado.")
        self.excel_file = excel_file
        self.xls = pd.ExcelFile(excel_file)

    def listar_folhas(self):
        print(f"Folhas no arquivo {self.excel_file}:")
        for name in self.xls.sheet_names:
            print(f"- {name}")

    def mostrar_cabecalhos(self, linhas=5):
        for sheet in self.xls.sheet_names:
            print(f"\n--- Folha: {sheet} ---")
            df = pd.read_excel(self.xls, sheet)
            print(df.head(linhas))

    def criar_agendamento_df(self, n=5):
        df_line = pd.read_excel(self.xls, 'line')
        agendamento_df = pd.DataFrame({
            'ramo': df_line[['De', 'Para']].head(n).values.tolist(),
            'duracao': [5]*n,
            'prioridade': [1]*n
        })
        return agendamento_df

    def criar_contingencia_df(self, inicio=5, fim=8):
        df_line = pd.read_excel(self.xls, 'line')
        contingencia_df = pd.DataFrame({
            'contingencia': range(1, fim-inicio+1),
            'from': df_line['De'].iloc[inicio:fim].values,
            'to': df_line['Para'].iloc[inicio:fim].values
        })
        return contingencia_df


if __name__ == '__main__':
    excel_file = 'SIN_45_barras_dataset.xlsx'
    if not os.path.exists(excel_file):
        print("Criando dataset base...")
        SmartGridSin45().create_sin45_dataset_file(excel_file)

    analise = AnaliseExploratoriaDados(excel_file)
    analise.listar_folhas()
    analise.mostrar_cabecalhos()

    print("\n--- Agendamento ---")
    print(analise.criar_agendamento_df())

    print("\n--- Contingência ---")
    print(analise.criar_contingencia_df())
