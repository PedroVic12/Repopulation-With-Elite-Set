import numpy as np
import pandapower as pp
import pandapower.networks as pw
import pandas as pd

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

import logging


logging.basicConfig(
    filename='logs.txt',
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w',
    level=logging.DEBUG
)

install()

class Logger:
    def __init__(self):
        self.console = Console(theme=Theme({
            "success": "bold green",
            "warning": "yellow",
            "error": "bold red",
            "info": "white"  # Added "info" level for default blue color
        }))

        self.logger = logging.getLogger()



    def log(self, message, level="info"):  # Changed default level to "info"
        """Logs a message with the specified level and color."""
        if level == "success":
            self.console.print(f"[success]{message}[/]")
            self.logger.info(message)
        elif level == "warning":
            self.console.print(f"[warning]{message}[/]")
            self.logger.warning(message)
        elif level == "error":
            self.console.print(f"[error]{message}[/]")
            self.logger.error(message)
        else:
            self.console.print(f"[info]{message}[/]") # Changed to "info" to use blue color



class RedeEletricaPandaPower:
    def __init__(self, network_name, debug=False):
        self.net = self.carregar_redes_padrao(network_name)
        self.debug = debug
        self.console = Logger()

        #metoodos
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

    def carregar_redes_padrao(self, network_name="14"):
        """Carrega redes padrão do pandapower."""
        if network_name == "14":
            network = pw.case14()
        elif network_name == "30":
            network = pw.case30()
        elif network_name == "57":
            network = pw.case57()
        elif network_name == "118":
            network = pw.case118()
        else:
            print("Rede não encontrada, forneça o número como string")
            network = None

        return network

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


    def show_status(self):

        if self.debug:
            print("="*80)
            print("Rede atual")
            print("="*80)

            print("\nStatus Linhas")
            display(self.net.line[["from_bus","to_bus","in_service"]])

            print("\nStatus Transformadores")
            display(self.net.trafo[["hv_bus","lv_bus","in_service"]])

            ## Barramentos
            #print("\nTensões nos Barramentos (pu):")
            #display(self.net.res_bus[['vm_pu']])

            ## linhas
            #print("\nPorcentagem de Carga nas Linhas (%):")
            #display(self.net.res_line[['loading_percent']])

            #print("\nPotência Aparente nas Linhas (MVA):")
            #display(self.net.res_line[['p_from_mw', 'q_from_mvar']])


            # transformadores
            #print("\nPotencia aparente nos transformadores")
            #display(self.net.res_trafo[['p_hv_mw', 'q_hv_mvar', 's_aparente_hv_mva', 'p_lv_mw', 'q_lv_mvar', 's_aparente_lv_mva']])


            #print("\nPorcentagem de Carga nos transformadores (%):")
            #display(self.net.res_trafo[['loading_percent']])

            #print("="*80)



    #! Otimização
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

            carregamento = row["loading_percent"] * 100
            limite_max = self.net.line.at[idx, "max_loading_percent"]

            if carregamento > limite_max:
                self.log("\n\nUltrapassou limite maximo nas linhas",level = "warning")
                self.log(f"{carregamento:.2f} > {limite_max} %",level = "warning")
                #RZ - as violações também devem considerar 100% = 1, deve-se dividir
                violacoes["loading_linhas"] += (carregamento - limite_max) / 100

        # Verificar carregamento dos transformadores
        for idx, row in self.net.res_trafo.iterrows():
            carregamento = row["loading_percent"] * 100
            limite_max = self.net.trafo.at[idx, "max_loading_percent"]

            if carregamento > limite_max:
                self.log("\n\nUltrapassou limite maximo nos transformadores",level = "warning")
                self.log(f"{carregamento:.2f} > {limite_max} %",level = "warning")
                #RZ - as violações também devem considerar 100% = 1, deve-se dividir
                violacoes["loading_trafos"] += (carregamento - limite_max) / 100

        #! TODO -> PASSAR OS PESOS NA ISNTANCIA DO OBJETO COM VALOR DEFAULT
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

    #! Pandapower New metodos
    def executar_fluxo_de_carga(self, fast = True):
        """
        Executa o fluxo de carga na rede elétrica usando o algoritmo Newton-Raphson.

        Retorna:
            bool: True se o fluxo de carga convergiu, False caso contrário.
        """
        try:
            pp.runpp(self.net, algorithm="nr", numba = fast)
            self.log("\nFluxo de potência executado com sucesso.",level = "success")

            return True
        except pp.LoadflowNotConverged:
            self.console.log("\nErro: Fluxo de potência não convergiu.", level = "error")
            Pdem = 99

            self.calcular_violacoes_fitness()


            return False

    def ajustar_cargas(self, perfil):
        """Ajusta as cargas conforme o perfil (1 = leve, 2 = médio, 3 = pesado)."""
        tipo = ""

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

        # usando o scaling
        #self.net.load["p_mw"] *= fator
        #self.net.load["q_mvar"] *= fator
        self.net.load.scaling = fator
        #self.net.gen['vm_pu'] = 1.045
        self.net.gen.scaling = fator

        self.log("Cargas ajustadas.", level = "success")

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


    #! Old Pandapower

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
