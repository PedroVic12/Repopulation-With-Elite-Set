import pandas as pd
import plotly.express as px
import streamlit as st
import json
from abc import ABC, abstractmethod
from streamlit_option_menu import option_menu
from DataExploration import DataExploration
from AlgoritimoEvolutivoRCE import AlgoritimoEvolutivoRCE
from Setup_rce import Setup


# Setup


class FileReader(ABC):
    @abstractmethod
    def read(self, file_path: str):
        pass


class ExcelFileReader(FileReader):
    def read(self, file_path: str):
        return pd.read_excel(file_path)


class JsonFileReader(FileReader):
    def read(self, file_path: str):
        with open(file_path, "r") as file:
            data = json.load(file)
        return pd.DataFrame(data)


class DataHandler:
    def __init__(self, file_reader: FileReader):
        self.file_reader = file_reader

    def load_data(self, file_path: str):
        return self.file_reader.read(file_path)


class dashPY:
    def __init__(self):
        self.dataframes = {}
        self.data_visual = DataExploration()

    def adicionar_tabela(self, nome: str, df: pd.DataFrame):
        self.dataframes[nome] = df

    def gerar_graficos_interativos(self, colunas):
        if len(colunas) < 3:
            st.write("Por favor, selecione ao menos três colunas.")
            return

        st.plotly_chart(px.histogram(self.df, x=colunas[0]))
        st.plotly_chart(px.line(self.df, x=colunas[1], y=colunas[2]))
        st.plotly_chart(px.bar(self.df, x=colunas[1], y=colunas[2]))

    def exibir_dataset(self):
        st.dataframe(self.df)

    def plot_interativo(self):
        st.title("Visualização de dados Alg Evolutivo")
        mes_selecionado = st.sidebar.multiselect(
            "Escolha a coluna", self.df.columns, placeholder="Selecione"
        )

        if mes_selecionado:
            fig = px.line(self.df, x="dias", y=mes_selecionado)
            st.plotly_chart(fig)
            st.write(self.df[mes_selecionado])

            col1, col2, col3 = st.columns(3)
            col1.bar_chart(self.df[mes_selecionado])
            col2.line_chart(self.df[mes_selecionado])
            col2.area_chart(self.df[mes_selecionado])
            col3.line_chart(self.df[mes_selecionado])

    def pagina1(self, pop_with_repopulation, logbook_with_repopulation, best_variables):
        st.title("Página 5: Visualização dos Resultados")
        self.data_visual.show_rastrigin_benchmark(
            logbook_with_repopulation, best_variables
        )
        x, y, z = self.data_visual.visualize(
            logbook_with_repopulation, pop_with_repopulation, repopulation=True
        )

        st.plotly_chart(px.scatter_3d(x=x, y=y, z=z))  # Ajuste conforme necessário
        avg, std = self.data_visual.statistics_per_generation_df(
            logbook_with_repopulation
        )
        st.write(avg)
        st.write(std)

    def pagina2(self):
        st.title("Página 2: Gráficos Interativos")
        colunas = st.multiselect(
            "Selecione as colunas para os gráficos", self.df.columns
        )
        if st.button("Gerar Gráficos"):
            self.gerar_graficos_interativos(colunas)

    def pagina3(self):
        st.title("Página 3: Plot Interativo")
        self.plot_interativo()

    def pagina4(self):
        st.title("Página 4: Todos os DataFrames")
        for nome, df in self.dataframes.items():
            st.subheader(f" {nome}")
            st.dataframe(df)


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


params = load_params(
    r"/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/parameters.json"
)

setup = Setup(params)
alg = AlgoritimoEvolutivoRCE(setup)
data_visual = ()

pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
    RCE=True,
    # fitness_function=rastrigin_decisionVariables,
    # decision_variables=(X, y),
)


def main():
    st.title("Visualização de Dados Interativos")

    def select_file():
        file_type = st.radio("Selecione o tipo de arquivo", ("Excel", "JSON"))
        file_path = st.text_input("Insira o caminho do arquivo:")

        if not file_path:
            st.write("Por favor, insira o caminho do arquivo.")
            return

        if file_type == "Excel":
            file_reader = ExcelFileReader()
        elif file_type == "JSON":
            file_reader = JsonFileReader()

        data_handler = DataHandler(file_reader)
        df = data_handler.load_data(file_path)

        # columns = st.multiselect("Selecione as colunas para os gráficos", df.columns)

    excel = "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/consumo_eletrico_agua.xlsx"

    st.title("Visualização de Dados Interativos")
    df = pd.read_excel(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/consumo_eletrico_agua.xlsx",
    )
    colunas = df.columns
    print(colunas)

    df.dropna()
    print(df)

    tabela_evolutiva = pd.read_excel(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/views/tabelas/parametros_evolutivos.xlsx"
    )
    tabela = pd.read_excel(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/views/tabelas/tabela_consolidada.xlsx"
    )
    tabela_resumo = pd.read_excel(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/views/tabelas/tabela_resumo.xlsx"
    )

    tabela_cv = pd.read_excel(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/assets/output/tabela_resumo_CV-21-06.xlsx"
    )

    dash = dashPY()
    dash.adicionar_tabela("Tabela Evolutiva", tabela_evolutiva)
    dash.adicionar_tabela("Tabela Consolidada", tabela)
    dash.adicionar_tabela("Tabela Resumo", tabela_resumo)

    dash.adicionar_tabela("Tabela CV", tabela_cv)
    # dash.adicionar_tabela("Tabela Inicial", df)

    selected = option_menu(
        menu_title="Menu",
        options=["Página 1", "Página 2", "Página 3", "Página 4"],
        icons=["house", "bar-chart", "line-chart", "table"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

    if selected == "Página 1":
        dash.pagina1(pop_with_repopulation, logbook_with_repopulation, best_variables)
    elif selected == "Página 2":
        dash.pagina2()
    elif selected == "Página 3":
        dash.pagina3()
    elif selected == "Página 4":
        dash.pagina4()


if __name__ == "__main__":
    main()
