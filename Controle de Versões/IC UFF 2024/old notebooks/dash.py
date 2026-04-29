import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Importando os dados
best_df_with_repopulation = pd.read_csv(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/assets/output/best_individuals_with_repopulation.csv"
)  # Altere para o nome do arquivo gerado
best_df_without_repopulation = pd.read_csv(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/assets/output/best_individuals_without_repopulation.csv"
)  # Altere para o nome do arquivo gerado

fitness_df_with_repopulation = pd.read_csv(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/assets/output/fitness_with_repopulation.csv"
)  # Altere para o nome do arquivo gerado
fitness_df_without_repopulation = pd.read_csv(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/assets/output/fitness_without_repopulation.csv"
)  # Altere para o nome do arquivo gerado


# Função para visualizar gráficos
def visualize_data(best_df, fitness_df, repopulation):
    st.title("Dashboard de Visualização")

    # Gráfico de linhas para Melhor Fitness e Média Fitness por Geração
    st.subheader("Melhor Fitness e Média Fitness por Geração")
    generations = best_df["Generations"]
    best_fitness = best_df["Best Solution"]
    avg_fitness = best_df["Media"]
    plt.plot(generations, best_fitness, label="Melhor Fitness")
    plt.plot(generations, avg_fitness, label="Média Fitness")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    plt.legend()
    st.pyplot()

    # Gráfico de barras para Fitness por Geração
    st.subheader("Fitness por Geração")
    plt.bar(fitness_df["Generations"], fitness_df["Fitness"], label="Fitness")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    st.pyplot()

    # Gráfico 3D para visualizar a população
    st.subheader("Visualização da População (Gráfico 3D)")
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    x_values = np.random.rand(10)
    y_values = np.random.rand(10)
    z_values = np.random.rand(10)
    ax.scatter(x_values, y_values, z_values, c="b", label="Population")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend()
    st.pyplot()


# Opções para escolher entre os dados com e sem repopulação
option = st.sidebar.selectbox(
    "Selecione uma opção:", ("Com Repopulação", "Sem Repopulação")
)

# Visualização dos dados com base na opção selecionada
if option == "Com Repopulação":
    visualize_data(
        best_df_with_repopulation, fitness_df_with_repopulation, repopulation=True
    )
elif option == "Sem Repopulação":
    visualize_data(
        best_df_without_repopulation,
        fitness_df_without_repopulation,
        repopulation=False,
    )
