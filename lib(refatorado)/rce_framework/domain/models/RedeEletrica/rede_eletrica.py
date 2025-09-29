import pandapower as pp
import pandapower.networks as pw
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

from pandapower.plotting import simple_plot, simple_plotly, pf_res_plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio



install()

class Logger:
    def __init__(self):
        self.console = Console(theme=Theme({
            "success": "bold green",
            "warning": "yellow",
            "error": "bold red",
            "info": "white"  # Added "info" level for default blue color
        }))




    def log(self, message, level="info"):  # Changed default level to "info"
        """Logs a message with the specified level and color."""
        if level == "success":
            self.console.print(f"\n[success]{message}[/]")
            #self.logger.info(message)
        elif level == "warning":
            self.console.print(f"[warning]{message}[/]")
            #self.logger.warning(message)
        elif level == "error":
            self.console.print(f"[error]{message}[/]")
            #self.logger.error(message)
        else:
            self.console.print(f"\n[info]{message}[/]") # Changed to "info" to use blue color




class RedeEletricaPandaPower:
    def __init__(self, network_name = "", debug=False , tabela_hash = None, tamanho_hash = 0):
        self.net = self.loading_networks_cases(network_name)
        self.debug = debug
        
        self.console = Logger()

        #metodos
        self.criar_mapeamento_ramos()

        # global
        self.pesos = {
            "tensao": {"min": 100, "max": 100},
            "loading_linhas": 100,
            "loading_trafos": 150,
            "demanda": 99,
        }
        self.agendamento = pd.DataFrame()
        self.contingencia= pd.DataFrame()
        
        
        ## UPGRADE HASH TABLE
        #! Inicializa a HashTable na instancia do Objeto !
        # if tamanho_hash > 0:
        #     self.tabela_hash = [-1] * tamanho_hash
        # else:
        #     self.tabela_hash = None
            
        # self.objectiveruns = 0
        # self.hashtablereads = 0

    def loading_networks_cases(self, network_name = "14"):
        #!todo -> Switch para as redes disponiveis na lib
        match network_name:
            case "14":
                self.network_name = "Case 14"
                
                network = pw.case14()
                


            case "30":
                #RZ não confundir com case30
                self.network_name = "Case 30"

                network = pw.case_ieee30()

            case "57":
                network = pw.case57()
                
                self.network_name = "Case 57"


            case "118":
                network = pw.case118()
                self.network_name ="Case 118"
                


            case "nova":
                network = pw.create_empty_network()
                #network_name = input("\nDigite o nome da sua rede que voce quer simular:  ")
                if network_name != "":
                    self.network_name = "Nova Rede (desconheçida)"
                else:
                    self.network_name = network_name


            case _:
                print("Rede não encontrada, forneça o numero como string como: IEEE 14 = '14'")
                print(f"\n\nRede '{network_name}' não reconhecida. Usando 'IEEE case14' para demosntração...")
                network = pw.case14()
                print("Carregando Rede Elétrica IEEE 14")
                #network = None

        return network

    #! uso de trafos, linhas e barramentos
    #===================================================================================
    def criar_mapeamento_ramos(self):
        """Mapeia pares de barramentos para índices de linhas e trafos"""
        self.mapeamento_ramos = {
            'linhas': {},
            'trafos': {}
        }

        # Linhas
        for idx, row in self.net.line.iterrows():
            key = tuple(sorted((row['from_bus'], row['to_bus'])))
            self.mapeamento_ramos['linhas'][key] = idx

        # Transformadores
        for idx, row in self.net.trafo.iterrows():
            key = tuple(sorted((row['hv_bus'], row['lv_bus'])))
            self.mapeamento_ramos['trafos'][key] = idx

        return self.mapeamento_ramos

    def resetar_rede(self):
        """Restaura a rede para o estado operacional religando todos os elementos."""
        self.net.line['in_service'] = True
        if not self.net.trafo.empty:
            self.net.trafo['in_service'] = True
            
    def aplicar_contingencia(self, tipo_elemento, elemento_id):
        """Aplica uma contingência desligando um elemento da rede."""
        if tipo_elemento == 'Linha' and elemento_id in self.net.line.index:
            self.net.line.loc[elemento_id, 'in_service'] = False
        elif tipo_elemento == 'Transformador' and elemento_id in self.net.trafo.index:
            self.net.trafo.loc[elemento_id, 'in_service'] = False

    def validar_dados(self, df_agendamento, df_contingencia):
        """Valida consistência dos dados antes de processar"""
        # Verifica colunas obrigatórias
        required_agendamento = ["ramo", "inicio", "duracao", "prioridade"]
        if not all(col in df_agendamento.columns for col in required_agendamento):
            #raise ValueError("Colunas faltantes no agendamento_df")
            print("Colunas faltantes no agendamento_df")


        # Verifica existência dos ramos
        for _, row in df_agendamento.iterrows():
            ramo = tuple(sorted(row['ramo']))
            if not (ramo in self.mapeamento_ramos['linhas'] or ramo in self.mapeamento_ramos['trafos']):
                #raise ValueError(f"Ramo {row['ramo']} não existe na rede")
                print(f"Ramo {row['ramo']} não existe na rede")

        self.agendamento = df_agendamento
        self.contingencia = df_contingencia


    def hashtableindex (self, carregamento, n_carregamentos, contingencia, n_contingencias, desligamentos):
        """"
        Recebe os dados do cenário e retorna o índice da tabela hash correspondente
        carregamento -> inteiro de 1 a numero de carregamentos
        n_carregamentos -> inteiro com o número total de carregamentos
        contingencia -> inteiro de 1 a numero de contingencias
        n_contingencias -> total de contingencias
        desligamentos -> vetor linha com ndeslig elementos booleanos
        """
        num_desligamentos= len(desligamentos)

        #converte o vetor binário em inteiro de forma eficiente
        #https://stackoverflow.com/questions/24560596/fastest-way-to-convert-a-binary-listor-array-into-an-integer-in-python
        digits = ['0', '1']

        k = int("".join([ digits[y] for y in desligamentos ]), 2)

        return (k * (n_carregamentos) * (n_contingencias) ) + ((carregamento-1) * (n_contingencias))  + (contingencia-1)


    #==============================================================================================================================================================

    #! UTILS
    def log(self, mensagem,level="info"):
        if self.debug:
            self.console.log(mensagem,level)

    def plot_rede_eletrica_status(self,  trafo_status, line_status):
        """Plota o status (ligado/desligado) dos transformadores e linhas em um gráfico de barras.

        Args:
            x: Dados para o eixo x.
            y: Dados para o eixo y.
            net: Objeto pandapower contendo os resultados da simulação.
            trafo_status: Array contendo o status (True/False) dos transformadores.
            line_status: Array contendo o status (True/False) dos linhas.
        """

        # Combinar os status de transformadores e linhas
        all_status = np.concatenate([trafo_status, line_status])

        # Criar um array de rótulos para o eixo x (nomes dos ramos)
        num_trafos = len(trafo_status)
        num_lines = len(line_status)
        x_labels = np.arange(1, num_trafos + num_lines + 1)

        # Criar o gráfico de barras
        fig, ax = plt.subplots(figsize=(10, 6))  # Ajustar o tamanho conforme necessário

        # Definir cores para ligado (verde) e desligado (vermelho)
        colors = ['g' if s else 'r' for s in all_status]

        # Criar as barras com as cores definidas
        bars = ax.bar(x_labels, np.ones_like(all_status), color=colors)

        # Configurar o gráfico
        ax.set_xlabel("Ramo")
        ax.set_ylabel("Status")
        ax.set_title("Status dos Transformadores e Linhas (Ligado/Desligado)")
        ax.set_xticks(x_labels)  # Definir os ticks do eixo x
        ax.set_yticks([1])  # Mostrar apenas o tick '1' no eixo y
        ax.set_yticklabels([''])  # Remover o rótulo '1' do eixo y

        # Ajustar a legenda para mostrar 'Transformador' e 'Linha'
        legend_labels = ['Ligado', 'Desligado']
        legend_handles = [bars[0], bars[-1] if not all_status[0] else bars[all_status.index(False)]]

        ax.legend(legend_handles, legend_labels, loc='best')  # Adicionar legenda

        plt.show()  # Mostrar o gráfico

    def plot_trafo_status_only(self,net):
        """Plota o status (ligado/desligado) dos transformadores e linhas em um gráfico de barras.

        Args:
            net: Objeto pandapower contendo os resultados da simulação.
        """

        # Extrair o status (in_service) dos transformadores e linhas
        trafo_status = net.trafo["in_service"].values
        line_status = net.line["in_service"].values

        # Combinar os status de transformadores e linhas
        all_status = np.concatenate([trafo_status, line_status])

        # Criar um array de rótulos para o eixo x (nomes dos ramos)
        num_trafos = len(trafo_status)
        num_lines = len(line_status)
        x_labels = np.arange(1, num_trafos + num_lines + 1)

        # Criar o gráfico de barras
        fig, ax = plt.subplots(figsize=(10, 6))  # Ajustar o tamanho conforme necessário

        # Definir cores para ligado (verde) e desligado (vermelho)
        colors = ['g' if s else 'r' for s in all_status]

        # Criar as barras com as cores definidas
        bars = ax.bar(x_labels, np.ones_like(all_status), color=colors)

        # Configurar o gráfico
        ax.set_xlabel("Ramo")
        ax.set_ylabel("Status")
        ax.set_title("Status de todas as Linhas (Ligado/Desligado)")
        ax.set_xticks(x_labels)  # Definir os ticks do eixo x
        ax.set_yticks([1])  # Mostrar apenas o tick '1' no eixo y
        ax.set_yticklabels([''])  # Remover o rótulo '1' do eixo y

        # Ajustar a legenda para mostrar 'Transformador' e 'Linha'
        legend_labels = ['Ligado', 'Desligado']
        legend_handles = [bars[0], bars[-1] if not all_status[0] else bars[all_status.index(False)]]

        ax.legend(legend_handles, legend_labels, loc='best')  # Adicionar legenda

        plt.show()  # Mostrar o gráfico

    def plot_trafo_status(self, net):
        """Plota o status (ligado/desligado) dos transformadores em um gráfico de barras.

        Args:
            net: Objeto pandapower contendo os resultados da simulação.
        """

        # Extrair os dados de loading_percent e status (in_service)
        loading_percent = net.res_trafo["loading_percent"].values
        status = net.trafo["in_service"].values

        # Criar um array de rótulos para o eixo x (nomes dos ramos)
        x_labels = np.arange(1, len(loading_percent) + 1)

        # Criar o gráfico de barras
        fig, ax = plt.subplots(figsize=(10, 6))  # Ajustar o tamanho conforme necessário
        bars = ax.bar(x_labels, loading_percent, color='b')  # Barras azuis para loading_percent

        # Ajustar as cores das barras para vermelho se o transformador estiver desligado
        for i, bar in enumerate(bars):
            if not status[i]:  # Se status for False (desligado)
                bar.set_color('r')

        # Configurar o gráfico
        ax.set_xlabel("Ramo")
        ax.set_ylabel("Loading Percent")
        ax.set_title("Status dos Transformadores")
        ax.set_xticks(x_labels)  # Definir os ticks do eixo x
        ax.legend([bars[0], bars[-1]], ['Ligado', 'Desligado'], loc='best')  # Adicionar legenda

        plt.show()  # Mostrar o gráfico


    def show_status(self, debug = False):
        
                    #! PLOT DO STATUS DAS LINHAS E TRANSFORMADORES
        try:

            # Plot do loading percente das linhas
            #self.plot_trafo_status_only(self.net)

            # Pega os dados estado e lgiados de linhas e trafos

            line_status = self.net.line["in_service"].values
            trafo_status = self.net.trafo["in_service"].values

            # plot que mostra as linhas ligadas
            self.plot_rede_eletrica_status( trafo_status, line_status)



            # print("\nStatus noTransformadores")
            #display(self.net.trafo[["hv_bus","lv_bus","in_service"]])
            #display(self.net.res_trafo[["loading_percent"]])

            #self.plot_trafo_status(self.net)
            
            
        except Exception as erro:
            print("Erro ao plotar tensões nas barras", erro)



        if self.debug:
            print("="*80)
            print("Rede atual")
            print("="*80)

            print("\nStatus Linhas")
            display(self.net.line[["from_bus","to_bus","in_service"]])
            #display(self.net.res_line[["loading_percent"]])


            ## Barramentos
            #print("\nTensões nos Barramentos (pu):")
            #display(self.net.res_bus[['vm_pu']])


            ## linhas
            #print("\nPorcentagem de Carga nas Linhas (%):")
            #display(self.net.res_line[['loading_percent']])



            #! PLOT DOS VALORES DE POTENCIA APARENTE POS FLUXO DE POTENCIA
            #self.plot_power_data()

            #print("\nPotência Aparente nas Linhas (MVA):")
            #display(self.net.res_line[['p_from_mw', 'q_from_mvar']])


            # transformadores
            #print("\nPotencia aparente nos transformadores")
            #display(self.net.res_trafo[['p_hv_mw', 'q_hv_mvar', 's_aparente_hv_mva', 'p_lv_mw', 'q_lv_mvar', 's_aparente_lv_mva']])


            #print("\nPorcentagem de Carga nos transformadores (%):")
            #display(self.net.res_trafo[['loading_percent']])

            #print("="*80)
            
    def plot_potencia_ativa_reativa(self):
        figs = []
        net = self.net
        output_file = f"./potencia_caso_{self.network_name}.html"
        
        #fig_diagrama = self.plot_diagrama_cenario()
        figs.append(pf_res_plotly(net))

        # === Gráfico 1: Potências ===
        fig_pot = make_subplots(rows=1, cols=1, subplot_titles=["Potências Ativa e Reativa"])
        if not net.line.empty:
            idx = np.arange(len(net.res_line))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_line['p_from_mw'], name="P Linhas (MW)", mode='lines'))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_line['q_from_mvar'], name="Q Linhas (MVAr)", mode='lines'))
        if not net.trafo.empty:
            idx = np.arange(len(net.res_trafo))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_trafo['p_hv_mw'], name="P Trafos (MW)", mode='lines'))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_trafo['q_hv_mvar'], name="Q Trafos (MVAr)", mode='lines'))
        if not net.load.empty:
            idx = np.arange(len(net.res_load))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_load['p_mw'], name="P Cargas (MW)", mode='lines'))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_load['q_mvar'], name="Q Cargas (MVAr)", mode='lines'))
        fig_pot.update_layout(title="Gráfico de Potências", xaxis_title="Índice", yaxis_title="Potência")

        figs.append(fig_pot)

        # === Gráfico 2: Tensões ===
        fig_tens = make_subplots(rows=1, cols=1, subplot_titles=["Tensões em pu"])
        idx_bus = np.arange(len(net.res_bus))
        fig_tens.add_trace(go.Scatter(x=idx_bus, y=net.res_bus['vm_pu'], name="Tensão Barras", mode='lines'))
        if not net.line.empty:
            idx_line = np.arange(len(net.res_line))
            fig_tens.add_trace(go.Scatter(x=idx_line, y=net.res_line['vm_from_pu'], name="Tensão Linhas", mode='lines'))
        fig_tens.update_layout(title="Gráfico de Tensões", xaxis_title="Índice", yaxis_title="Tensão (pu)")

        figs.append(fig_tens)
        
        # === Exportar tudo para HTML ===
        html_parts = ""
        for fig in figs:
            html_parts += pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

        with open(output_file, "w") as f:
            f.write(f"""
            <html>
                <head><title>Relatório Elétrico</title></head>
                <body>
                    <h1>Cáculo de Potencia da Rede - {self.network_name} </h1>
                    {html_parts}
                </body>
            </html>
            """)
            


    def plot_all_results_to_html(self, output_file="relatorio_eletrico.html"):
        """
        Gera três gráficos interativos separados (potência, tensão, corrente) e exporta para um único HTML.
        """
        figs = []
        net = self.net
        
        #fig_diagrama = self.plot_diagrama_cenario()
        figs.append(pf_res_plotly(net))


        # === Gráfico 1: Potências ===
        fig_pot = make_subplots(rows=1, cols=1, subplot_titles=["Potências Ativa e Reativa"])
        if not net.line.empty:
            idx = np.arange(len(net.res_line))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_line['p_from_mw'], name="P Linhas (MW)", mode='lines'))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_line['q_from_mvar'], name="Q Linhas (MVAr)", mode='lines'))
        if not net.trafo.empty:
            idx = np.arange(len(net.res_trafo))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_trafo['p_hv_mw'], name="P Trafos (MW)", mode='lines'))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_trafo['q_hv_mvar'], name="Q Trafos (MVAr)", mode='lines'))
        if not net.load.empty:
            idx = np.arange(len(net.res_load))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_load['p_mw'], name="P Cargas (MW)", mode='lines'))
            fig_pot.add_trace(go.Scatter(x=idx, y=net.res_load['q_mvar'], name="Q Cargas (MVAr)", mode='lines'))
        fig_pot.update_layout(title="Gráfico de Potências", xaxis_title="Índice", yaxis_title="Potência")

        figs.append(fig_pot)

        # === Gráfico 2: Tensões ===
        fig_tens = make_subplots(rows=1, cols=1, subplot_titles=["Tensões em pu"])
        idx_bus = np.arange(len(net.res_bus))
        fig_tens.add_trace(go.Scatter(x=idx_bus, y=net.res_bus['vm_pu'], name="Tensão Barras", mode='lines'))
        if not net.line.empty:
            idx_line = np.arange(len(net.res_line))
            fig_tens.add_trace(go.Scatter(x=idx_line, y=net.res_line['vm_from_pu'], name="Tensão Linhas", mode='lines'))
        fig_tens.update_layout(title="Gráfico de Tensões", xaxis_title="Índice", yaxis_title="Tensão (pu)")

        figs.append(fig_tens)

        # === Gráfico 3: Correntes ===
        fig_corr = make_subplots(rows=1, cols=1, subplot_titles=["Correntes Elétricas"])
        if not net.line.empty:
            fig_corr.add_trace(go.Bar(x=np.arange(len(net.res_line)), y=net.res_line['i_ka'], name="Corrente Linhas (kA)"))
        if not net.trafo.empty:
            fig_corr.add_trace(go.Bar(x=np.arange(len(net.res_trafo)), y=net.res_trafo['i_hv_ka'], name="Corrente Trafos (kA)"))
        fig_corr.update_layout(title="Gráfico de Correntes", xaxis_title="Índice", yaxis_title="Corrente (kA)")

        figs.append(fig_corr)

        # === Exportar tudo para HTML ===
        html_parts = ""
        for fig in figs:
            html_parts += pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

        with open(output_file, "w") as f:
            f.write(f"""
            <html>
                <head><title>Relatório Elétrico</title></head>
                <body>
                    <h1>Relatório de Resultados Elétricos - {self.network_name} </h1>
                    {html_parts}
                </body>
            </html>
            """)

        print(f"✅ Relatório gerado com sucesso: {output_file}")



    def plot_power_data(self, index = None):
        """Plota os dados de potência dos barramentos, linhas e transformadores em um gráfico de linhas.

        Args:
            index: Um array contendo os valores do índice da série temporal (tempo ou número da iteração).
        """
        print("Tentativa do primeiro plot com tensões e potencias de linhas, trafos e barras")
        try:
            #index = np.arange(len(self.net.res_line['p_from_mw']))
            # Extrair os dados de cada elemento da rede com nomes mais descritivos
            line_p_from_mw_data = self.net.res_line['p_from_mw'].values

            index = line_p_from_mw_data


            line_q_from_mvar_data = self.net.res_line['q_from_mvar'].values
            trafo_p_hv_mw_data = self.net.res_trafo['p_hv_mw'].values
            trafo_q_hv_mvar_data = self.net.res_trafo['q_hv_mvar'].values
            tensoes_barramentos = self.net.res_bus['vm_pu'].values
            tensoes_linhas = self.net.res_line['vm_from_pu'].values
            
            #trafo_s_aparente_hv_mva_data = self.net.res_trafo['s_aparente_hv_mva'].values
            #time_series = self.net['time'].values  # Or self.net['iteration'].values
            #print(time_series)

            fig, ax = plt.subplots(figsize=(14, 8))

                    # === PLOTAGEM DAS LINHAS ===
            if not self.net.line.empty:
                        index_line = np.arange(len(self.net.res_line))
                        ax.plot(index_line, self.net.res_line['p_from_mw'], label='P Ativa Linhas (MW)', color='blue')
                        ax.plot(index_line, self.net.res_line['q_from_mvar'], label='Q Reativa Linhas (MVAr)', color='red')
                        ax.plot(index_line, self.net.res_line['vm_from_pu'], label='Tensão Linhas (pu)', color='cyan')
                        #ax.plot(index_line, self.net.res_line['i_ka'], label='Corrente Linhas (kA)', color='darkblue')

                    # === PLOTAGEM DOS TRANSFORMADORES ===
            if not self.net.trafo.empty:
                        index_trafo = np.arange(len(self.net.res_trafo))
                        ax.plot(index_trafo, self.net.res_trafo['p_hv_mw'], label='P Ativa Trafos (MW)', color='green')
                        ax.plot(index_trafo, self.net.res_trafo['q_hv_mvar'], label='Q Reativa Trafos (MVAr)', color='orange')
                        #ax.plot(index_trafo, self.net.res_trafo['i_hv_ka'], label='Corrente Trafos (kA)', color='gold')

                    # === PLOTAGEM DAS BARRAS ===
            index_bus = np.arange(len(self.net.res_bus))
            ax.plot(index_bus, self.net.res_bus['vm_pu'], label='Tensão Barras (pu)', color='purple')
            #ax.plot(index_bus, self.net.res_bus['va_degree'], label='Ângulo de Fase (°)', color='magenta')

                    # === PLOTAGEM DAS CARGAS ===
            if not self.net.load.empty:
                index_load = np.arange(len(self.net.res_load))
                ax.plot(index_load, self.net.res_load['p_mw'], label='P Carga (MW)', color='darkgreen')
                ax.plot(index_load, self.net.res_load['q_mvar'], label='Q Carga (MVAr)', color='brown')

            ax.set_title("⚡ Dados Elétricos da Simulação Completa")
            ax.set_xlabel("Índice do Elemento")
            ax.set_ylabel("Valor")
            ax.grid(True)
            ax.legend()
            plt.tight_layout()
            plt.show()


        
        except Exception as e:
            print("Erro ao plotar os dados de potência:", e)
            self.console.log(f"Erro ao plotar os dados de potência: {e}", level="error")

    #! Funções de Graficos
    def plot_diagrama_cenario(self, net = None):
        if net is None:
            net = self.net
            
        fig = pf_res_plotly(net)
        return fig

    #! Otimização com Pandapower Métodos para Analise de contigencia com Casos IEEE

    def calcular_violacoes_fitness(self):
        """
        Calcula as violações nos barramentos, linhas e transformadores.

        Considerando um peso para cada grandeza : dois pesos para tensão (max e min) e outro para loading_percent das linhas.

        Somar (valor - limite max ou limite min - valor) para calcular a aptidão daquele cenário.

        Retornar o somatório de todas as violações, mas ao soma cada violação você deve multiplicar por um peso para determinar a aptidão do cenário.

        """
        violacoes = {
            "tensao_barramentos_min": 0,
            "tensao_barramentos_max": 0,
            "loading_linhas": 0,
            "loading_trafos": 0,
        }

        # Verificar tensões nos barramentos (pu) - check
        for idx, row in self.net.res_bus.iterrows():
            # Certifique-se de que a tensão está em pu
            tensao_pu = row["vm_pu"]

            limite_max = self.net.bus.at[idx, "max_vm_pu"]
            limite_min = self.net.bus.at[idx, "min_vm_pu"]

            if tensao_pu > limite_max:
                violacoes["tensao_barramentos_max"] += tensao_pu - limite_max
            elif tensao_pu < limite_min:
                violacoes["tensao_barramentos_min"] += limite_min - tensao_pu

        # Verificar carregamento das linhas
        for idx, row in self.net.res_line.iterrows():

            carregamento = row["loading_percent"] #* 100
            limite_max = self.net.line.at[idx, "max_loading_percent"]

            if carregamento > limite_max:
                self.log("\n\nUltrapassou limite maximo nas linhas",level = "warning")
                self.log(f"{carregamento:.2f} > {limite_max} %",level = "warning")
                #RZ - as violações também devem considerar 100% = 1, deve-se dividir
                violacoes["loading_linhas"] += (carregamento - limite_max) #/ 100

        # Verificar carregamento dos transformadores
        for idx, row in self.net.res_trafo.iterrows():
            carregamento = row["loading_percent"] #* 100
            limite_max = self.net.trafo.at[idx, "max_loading_percent"]

            if carregamento > limite_max:
                self.log("\n\nUltrapassou limite maximo nos transformadores",level = "warning")
                self.log(f"{carregamento:.2f} > {limite_max} %",level = "warning")
                #RZ - as violações também devem considerar 100% = 1, deve-se dividir
                violacoes["loading_trafos"] += (carregamento - limite_max) #/ 100

        #! TODO -> PASSAR OS PESOS NA INSTANCIA DO OBJETO COM VALOR DEFAULT
        """
        Pesos das violações : (Pdem=99,Pv = 100, Pn = 100 e Pe = 150)
        onde PV é a violação de tensão max e min,
        Pdem é para não convergência do fluxo
        Pn e Pe são para o fluxo de potência (pode usar só Pn que depois explico o que é Pe).
        """


        fitness = (
            self.pesos["tensao"]["min"] * violacoes["tensao_barramentos_min"]
            + self.pesos["tensao"]["max"] * violacoes["tensao_barramentos_max"]
            + self.pesos["loading_linhas"] * violacoes["loading_linhas"]
            + self.pesos["loading_trafos"] * violacoes["loading_trafos"]
        )

        #pega as violacoes e transforma em um DF
        violacoes_df = pd.DataFrame([violacoes])

        if self.debug:
            print("\nTotal de violações e salvando num banco de dados...")
            display(violacoes_df)
            self.console.log(f"\n\nAptidão do cenário nos barramentos, linhas e transformadores ", level = "success")
            self.console.log(f"VIOLAÇÃO TOTAL  = {fitness:.2f}\n", level = "success")

        return fitness, violacoes_df


    def calcular_perfil(self,j, ls, le, ms, me, hs, he):
        """
        Calcula o perfil de carregamento (leve, médio ou pesado) para a hora `j`.

        Args:
            j (int): Hora atual.
            ls, le, ms, me, hs, he (int): Limites de horários para os perfis de carga.

        Returns:
            int: Perfil de carregamento (1 = leve, 2 = padrão, 3 = pesado).
            perfil de carga media é igual IEEE_14
            perfil de carga pesada = multiplicar todas as potencias ativas e reativas, identificando os elementos das estruturas de self.net da classe RedeEletrica do pandapower

        """
        if ls <= j % 24 < le:
            return 1  # Leve
        elif ms <= j % 24 < me:
            return 2  # Médio
        elif hs <= j % 24 < he:
            return 3  # Pesado
        return 0  # Fora dos horários definidos


    def avalia_cenarios(self, horas: int, hora_inicio: list, duracao: list, ls, le, ms, me, hs, he , debug = False):
        """
        Args:
            horas (int): Horas de duração da janela de tempo.
            hora_inicio (list): Vetor de horários iniciais dos desligamentos (valores de 0 a m-1).
            duracao (list): Vetor de duração em horas de cada desligamento.
            ls, le, ms, me, hs, he (int): Limites iniciais e finais dos horários de carregamento leve, médio e pesado.

        Returns:
            list: Matriz que armazena todos os cenários do agendamento.
        """

        matriz_cenarios = []
        num_desligamentos = len(hora_inicio)

        # Ajusta limite da janela de tempo se algum desligamento terminar fora da janela
        for i in range(num_desligamentos):
            if horas < (hora_inicio[i] + duracao[i]):
                horas = hora_inicio[i] + duracao[i]

        # Inicializa matrizes auxiliares
        matriz_desligamentos_horas = np.zeros((num_desligamentos, horas), dtype=int)
        matriz_horas = np.zeros(horas, dtype=int)

        # =================== Avaliando desligamentos por hora =================
        for j in range(horas):  # Para cada hora
            for k in range(num_desligamentos):  # Para cada desligamento
                if hora_inicio[k] <= j < (hora_inicio[k] + duracao[k]):
                    matriz_desligamentos_horas[k, j] = 1
                matriz_horas[j] += matriz_desligamentos_horas[k, j] * (2 ** k)

        # =================== Avaliando cenários =================
        for horario in range(horas):
            if horario == 0:  # Condição inicial
                if matriz_horas[horario] > 0:
                    # Se há pelo menos um desligamento ativo
                    perfil = self.calcular_perfil(horario, ls, le, ms, me, hs, he)
                    matriz_cenarios.append([perfil] + matriz_desligamentos_horas[:, horario].tolist())
            else:
                if matriz_horas[horario] != matriz_horas[horario - 1] and matriz_horas[horario] > 0:
                    # Nova topologia
                    perfil = self.calcular_perfil(horario, ls, le, ms, me, hs, he)
                    matriz_cenarios.append([perfil] + matriz_desligamentos_horas[:, horario].tolist())
                else:
                    # Mesmo cenário, mas perfil pode mudar
                    if horario - 1 in [ms, hs] and matriz_cenarios:  # Verifica se matriz_cenarios não está vazia
                        perfil = self.calcular_perfil(horario, ls, le, ms, me, hs, he)
                        matriz_cenarios[-1][0] = max(matriz_cenarios[-1][0], perfil)

        if self.debug:
            self.log("\nMatriz Cenarios:")
            for linha in matriz_cenarios:
                self.log(linha)
            self.log(f"Avaliando um total de {len(matriz_cenarios)} cenários ")


        return matriz_cenarios

    def executar_fluxo_de_potencia(self, fast = True):
        """
        Executa o fluxo de carga na rede elétrica usando o algoritmo Newton-Raphson.
        fast = True faz o numba-python rodar em paralelo o algoritmo

        Retorna:
            bool: True se o fluxo de carga convergiu, False caso contrário.
        """
        
        
        try:
            pp.runpp(self.net, algorithm="nr", numba = True)
            self.log("Fluxo de potência executado com sucesso!",level = "success")
            #print("\n [DEBUG SIMULATOR]Fluxo de potência executado com sucesso!")
            return True
        except pp.LoadflowNotConverged:
            self.console.log("Erro: Fluxo de potência não convergiu...", level = "error")
            Pdem = 99
            print(f"\nATENÇÃO: CASO NAO CONVERGENTE! Penalidade de não convergência do fluxo de potência aplicada: {Pdem}\n")
            self.calcular_violacoes_fitness()
            return False

    def ajustar_cargas(self, perfil):
        """Ajusta as cargas conforme o perfil (1 = leve, 2 = médio, 3 = pesado)."""
        tipo = " "

        if perfil == 1:
            fator = 0.941  # Carga leve

            tipo = "leve"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")

        elif perfil == 2:
            fator = 1.0  # Carga média (IEEE14)

            tipo = "media"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")

        elif perfil == 3:
            fator = 1.177  # Carga pesada

            tipo = "pesada"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")

        else:
            fator = 1.0  # Perfil padrão (IEEE14)

            tipo = "padrão"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")

        #! TODO -> usando o scaling
        #self.net.load["p_mw"] *= fator
        #self.net.load["q_mvar"] *= fator
        self.net.load.scaling = fator
        #self.net.gen['vm_pu'] = 1.045
        self.net.gen.scaling = fator

        #!self.log("\nTodas as Cargas ajustadas.", level = "success")

    def desligar_elementos_agendamento(self, estados):
        """Desliga os elementos (linhas e trafos) com base no cenário."""

        linhas_desligar = []
        trafos_desligar = []

        for i, estado in enumerate(estados):
            if estado == 1:  # Verifica se o ramo deve ser desligado

                ramo = self.agendamento.iloc[i]["ramo"]

                #ramo = agendamento_df.iloc[i]["ramo"]  # Obtém o ramo da tabela
                #self.log("Ramo selecionado",ramo)

                for k in range(len(self.net.line)):
                    # TODO Verifica se o ramo é uma linha ou um transformador
                    if (self.net.line["from_bus"][k] == ramo[0] and self.net.line["to_bus"][k] == ramo[1]) or (self.net.line["from_bus"][k] == ramo[1] and self.net.line["to_bus"][k] == ramo[0] ):
                        linhas_desligar.append(ramo)  # Adiciona o ramo à lista de linhas

                for k in range(len(self.net.trafo)):
                    if (self.net.trafo["hv_bus"][k] == ramo[0] and self.net.trafo["lv_bus"][k] == ramo[1]) or (self.net.trafo["hv_bus"][k] == ramo[1] and self.net.trafo["lv_bus"][k] == ramo[0] ):
                        trafos_desligar.append(ramo)  # Adiciona o ramo à lista de trafos

        self.log(f"\n\nLinhas a serem desligadas: {linhas_desligar}")
        self.log(f"Trafos a serem desligados: {trafos_desligar}\n")

        # Desliga as linhas e trafos encontrados
        self.desligar_elementos(linhas_desligar, trafos_desligar)



    def desligar_contingencia(self, ramo):
        linhas_desligar = []
        trafos_desligar = []

        self.log("Ramo selecionado",ramo)

        for k in range(len(self.net.line)):
            # TODO Verifica se o ramo é uma linha ou um transformador
            if (self.net.line["from_bus"][k] == ramo[0] and self.net.line["to_bus"][k] == ramo[1]) or (self.net.line["from_bus"][k] == ramo[1] and self.net.line["to_bus"][k] == ramo[0] ):
                    linhas_desligar.append(ramo)  # Adiciona o ramo à lista de linhas

        for k in range(len(self.net.trafo)):
            if (self.net.trafo["hv_bus"][k] == ramo[0] and self.net.trafo["lv_bus"][k] == ramo[1]) or (self.net.trafo["hv_bus"][k] == ramo[1] and self.net.trafo["lv_bus"][k] == ramo[0] ):
                    trafos_desligar.append(ramo)  # Adiciona o ramo à lista de trafos

        self.log(f"\n\nLinhas a serem desligadas: {linhas_desligar}")
        self.log(f"Trafos a serem desligados: {trafos_desligar}\n")

        # Desliga as linhas e trafos encontrados
        self.desligar_elementos(linhas_desligar, trafos_desligar)

    def desligar_elementos(self, linhas_desligar, trafos_desligar):
        # Itera pelas linhas a serem desligadas e as desliga na rede
        if not linhas_desligar:
            self.log("Nenhuma linha para desligar")

        else:
            for l in linhas_desligar:

                # Encontra o índice da linha com base em from_bus e to_bus
                index_linha = self.net.line.loc[(self.net.line['from_bus'] == l[0]) & (self.net.line['to_bus'] == l[1])].index

                # Verifica se o índice foi encontrado (CORRIGIDO AQUI PVRV)
                if not index_linha.empty:
                    # Desliga a linha usando o índice encontrado
                    self.net.line.loc[index_linha, 'in_service'] = False

                    #print(f"Linha {l} desligada com sucesso.")


                else:
                    print(f"Linha {l} não encontrada na rede.")


        # Itera pelos transformadores a serem desligados e os desliga na rede
        if not trafos_desligar:
            self.log("Nenhum transformador para desligar")
        else:
            for t in trafos_desligar:

                # Encontra o índice da linha com base em from_bus e to_bus
                index_trafo = self.net.trafo.loc[(self.net.trafo['hv_bus'] == t[0]) & (self.net.trafo['lv_bus'] == t[1])].index

                # Verifica se o índice foi encontrado
                if not index_trafo.empty:
                    # Desliga a linha usando o índice encontrado
                    self.net.trafo.loc[index_trafo, 'in_service'] = False

                    #print(f"Transformador {t} desligado com sucesso.")

                else:
                    print(f"Transformador {t} não encontrado na rede.")


    #! Funções matematicas
    def calcular_potencia_aparente_trafos(self):
        """Calcula a potência aparente nos transformadores."""
        if not self.net.res_trafo.empty:
            if 's_aparente_hv_mva' not in self.net.res_trafo.columns:
                self.net.res_trafo['s_aparente_hv_mva'] = 0
            if 's_aparente_lv_mva' not in self.net.res_trafo.columns:
                self.net.res_trafo['s_aparente_lv_mva'] = 0

            # Calculando potência aparente para alta e baixa tensão
            potencia_high_tensao = (self.net.res_trafo['p_hv_mw']**2 + self.net.res_trafo['q_hv_mvar']**2)**0.5
            potencia_baixa_tensao = (self.net.res_trafo['p_lv_mw']**2 + self.net.res_trafo['q_lv_mvar']**2)**0.5

            return potencia_high_tensao, potencia_baixa_tensao
        else:
            print("Nenhum transformador na rede para calcular potência aparente.")
            return []

    def calcular_potencia_aparente_linhas(self):
        """Calcula a potência aparente nas linhas."""
        return (self.net.res_line['p_from_mw']**2 + self.net.res_line['q_from_mvar']**2)**0.5


    def religar_todos_os_ramos_agendamento(self):
        """Religa todos os ramos (linhas e transformadores) da rede elétrica."""
        # Religa todas as linhas
        self.net.line['in_service'] = True

        # Religa todos os transformadores
        self.net.trafo['in_service'] = True

        self.log("Todos os ramos religados.", level="success")



    def imprimir_resultados(self):
        """Retorna um array com todos os dados da rede elétrica"""
        dataframe = pd.DataFrame()

        # Calculo de potencia e colocando uma nova tabela no pandapower
        high_power_transformador, lower_power_transformador = self.calcular_potencia_aparente_trafos()
        fluxo_potencia_aparente_linhas = self.calcular_potencia_aparente_linhas()

        self.net.res_trafo['s_aparente_hv_mva'] = high_power_transformador
        self.net.res_trafo['s_aparente_lv_mva'] =  lower_power_transformador

        if self.debug:

            self.show_status()


        dataframe["tensao_nos_barramentos"] =  self.net.res_bus[['vm_pu']]
        dataframe["potencia_aparente_nas_linhas"] =  fluxo_potencia_aparente_linhas
        dataframe["porcentagem_de_carga_nas_linhas"] =  self.net.res_line[['loading_percent']]
        dataframe["potencia_aparente_nos_transformadores"] =  self.net.res_trafo[['p_hv_mw']]
        dataframe["porcentagem_de_carga_nos_transformadores"] =  self.net.res_trafo[['loading_percent']]

        dataframe.to_excel("dados_rede_eletrica.xlsx")
        self.log("\n\n\nDados da rede eletrica em formato de tabela excel disponivel!")

        return dataframe


    #!####################
    # Funções de simulações para pandapower simples
    def create_network(self):
        return pp.create_empty_network()

    def add_barras(self,net, barras):
        for barra in barras:
            pp.create_bus(net, name=barra["nome"], vn_kv=barra["tensao"], index=barra["id"])

    def add_ext_grid(self, net, bus, vm_pu, name):
        pp.create_ext_grid(net, bus=bus, vm_pu=vm_pu, name=name)

    def add_linhas(self, net, linhas):
        for linha in linhas:
            pp.create_line_from_parameters(
                net,
                from_bus=linha["de"],
                to_bus=linha["para"],
                length_km=linha["comprimento_km"],
                r_ohm_per_km=linha["r_ohm_per_km"],
                x_ohm_per_km=linha["x_ohm_per_km"],
                c_nf_per_km=linha["c_nf_per_km"],
                max_i_ka=linha["max_i_ka"],
                name=f"Linha {linha['de']} -> {linha['para']}",
            )

    def add_cargas(self, net, cargas):
        for carga in cargas:
            pp.create_load(net, bus=carga["bus"], p_mw=carga["p_mw"], q_mvar=carga["q_mvar"], name=carga["nome"])

    def add_geradores(self, net, geradores):
        for gerador in geradores:
            pp.create_sgen(net, bus=gerador["bus"], p_mw=gerador["p_mw"], vm_pu=gerador["vm_pu"], name=gerador["nome"])



    def simulate_network_functional(self):
        net = self.create_network()

        barras = [
            {"id": 0, "nome": "Barra 1", "tensao": 20.0},
            {"id": 1, "nome": "Barra 2", "tensao": 20.0},
            {"id": 2, "nome": "Barra 3", "tensao": 20.0},
            {"id": 3, "nome": "Barra 4", "tensao": 20.0},
        ]
        self.add_barras(net, barras)

        self.add_ext_grid(net, bus=0, vm_pu=1.0, name="Slack")

        linhas = [
            {"de": 0, "para": 1, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
            {"de": 1, "para": 2, "r_ohm_per_km": 0.02, "x_ohm_per_km": 0.04, "c_nf_per_km": 15, "max_i_ka": 0.2, "comprimento_km": 1.5},
            {"de": 2, "para": 3, "r_ohm_per_km": 0.015, "x_ohm_per_km": 0.035, "c_nf_per_km": 12, "max_i_ka": 0.2, "comprimento_km": 1.2},
        ]
        self.add_linhas(net, linhas)

        cargas = [
            {"bus": 1, "p_mw": 0.02, "q_mvar": 0.01, "nome": "Carga 1"},
            {"bus": 2, "p_mw": 0.03, "q_mvar": 0.015, "nome": "Carga 2"},
        ]
        self.add_cargas(net, cargas)

        geradores = [
            {"bus": 3, "p_mw": 0.05, "vm_pu": 1.02, "nome": "Gerador PV"},
        ]
        self.add_geradores(net, geradores)

        net = self.executar_fluxo_de_potencia(net)

        print("Resultados das Barras:")
        print(net.res_bus)

        print("\nResultados das Linhas:")
        print(net.res_line)

        print("\nResultados das Cargas:")
        print(net.res_load)

        return net
    
    
    
def main_rede_eletrica(simulate = False):
    print("iniciando a simulação de Rede Eleticas...")
    
    CASO = "14"  # Exemplo de caso, pode ser alterado para outros casos como "30", "57", etc.
    
    network_modelada = RedeEletricaPandaPower(CASO)
        
    
    if simulate:
        print(f"[debug] da classe Model RedeEletricaPandapower =  Simulação {network_modelada.network_name} iniciada")
        network_modelada.ajustar_cargas(perfil = 2)  # Ajusta para o perfil médio (IEEE 14)
        network_modelada.executar_fluxo_de_potencia(fast = True)
        #network.show_status(debug = True)
        #network.imprimir_resultados() 
        network_modelada.plot_power_data()
        network_modelada.plot_potencia_ativa_reativa()
        network_modelada.plot_all_results_to_html(output_file=f"./relatorio_eletrico_{network_modelada.network_name}.html")
            #network_modelada.simulate_network_functional()

    
#main_rede_eletrica()




























