import numpy as np
import sympy as sp
from scipy.integrate import odeint
import matplotlib.pyplot as plt
import pandas as pd

# =============================================================================
# Classe Base para Circuitos Elétricos
# =============================================================================
class Circuito:
    """
    Classe base para a modelagem de circuitos elétricos.
    Define a estrutura e os métodos comuns que os circuitos específicos herdarão.
    """
    def __init__(self, nome="Circuito Genérico"):
        self.nome = nome
        self.componentes = {}
        self.t = sp.symbols('t') # Variável simbólica para o tempo
        self.equacao_simbolica = None
        self.funcao_transferencia = None
        self.resultados_simulacao = None

    def adicionar_componente(self, nome, valor):
        """Adiciona um componente ao circuito."""
        self.componentes[nome] = valor
        print(f"Componente '{nome}' com valor {valor} adicionado.")

    def exibir_componentes(self):
        """Exibe os componentes do circuito."""
        print(f"\n--- Componentes do Circuito: {self.nome} ---")
        for nome, valor in self.componentes.items():
            print(f"- {nome}: {valor}")
        print("------------------------------------------")

    def obter_funcao_transferencia(self):
        """Método placeholder para a função de transferência."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse.")

    def resolver_edo(self):
        """Método placeholder para resolver a EDO."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse.")

    def plotar_resultados(self):
        """Plota os resultados da simulação usando Matplotlib."""
        if self.resultados_simulacao is None:
            print("Nenhuma simulação foi executada ainda. Execute `resolver_edo` primeiro.")
            return

        df = self.resultados_to_dataframe()
        print("\n--- Plotando Resultados da Simulação ---")

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        for coluna in df.columns:
            if coluna != 'Tempo (s)':
                ax.plot(df['Tempo (s)'], df[coluna], label=coluna)

        ax.set_title(f'Análise Temporal do {self.nome}', fontsize=16)
        ax.set_xlabel('Tempo (s)', fontsize=12)
        ax.set_ylabel('Amplitude (V, A)', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True)
        plt.tight_layout()
        plt.show()

    def resultados_to_dataframe(self):
        """Converte o dicionário de resultados em um DataFrame do Pandas."""
        if self.resultados_simulacao is None:
            print("Nenhuma simulação foi executada.")
            return None
        return pd.DataFrame(self.resultados_simulacao)

# =============================================================================
# Classe Específica para Circuito RLC Série (Exemplo)
# =============================================================================
class CircuitoRlcSerie(Circuito):
    """
    Modelo de um circuito RLC Série.
    Herda de 'Circuito' e implementa a lógica específica para
    análise de resposta ao degrau (CC) e resposta a uma senóide (CA).
    """
    def __init__(self, R, L, C, nome="Circuito RLC Série"):
        super().__init__(nome)
        self.adicionar_componente('Resistor (R)', f"{R} Ω")
        self.adicionar_componente('Indutor (L)', f"{L} H")
        self.adicionar_componente('Capacitor (C)', f"{C} F")
        self.R = R
        self.L = L
        self.C = C
        self._definir_equacao_simbolica()

    def _definir_equacao_simbolica(self):
        """
        Define a EDO do circuito RLC série de forma simbólica com Sympy.
        A EDO para a corrente i(t) é: L * i''(t) + R * i'(t) + (1/C) * i(t) = v'(t)
        Usaremos a carga q(t) para simplificar: L*q''(t) + R*q'(t) + (1/C)*q(t) = v(t)
        Onde i(t) = q'(t).
        """
        q = sp.Function('q')(self.t)
        v_in = sp.Function('v_in')(self.t)

        # L*q'' + R*q' + (1/C)*q = v_in(t)
        self.equacao_simbolica = sp.Eq(
            self.L * q.diff(self.t, 2) + self.R * q.diff(self.t, 1) + (1/self.C) * q,
            v_in
        )
        print("\n--- EDO Simbólica (em termos da carga q(t)) ---")
        sp.pprint(self.equacao_simbolica)
        print("-------------------------------------------------")


    def obter_funcao_transferencia(self, saida='vc'):
        """
        Calcula a função de transferência H(s) = Saida(s) / Entrada(s).
        A saída pode ser a tensão no capacitor (Vc), no indutor (Vl) ou no resistor (Vr).
        """
        s = sp.symbols('s')
        # Impedâncias no domínio de Laplace
        Z_R = self.R
        Z_L = s * self.L
        Z_C = 1 / (s * self.C)
        Z_total = Z_R + Z_L + Z_C

        # I(s) = V_in(s) / Z_total(s)
        # Vc(s) = I(s) * Zc = V_in(s) * Zc / Z_total
        # Vr(s) = I(s) * Zr = V_in(s) * Zr / Z_total
        # Vl(s) = I(s) * Zl = V_in(s) * Zl / Z_total

        if saida.lower() == 'vc':
            numerador = Z_C
        elif saida.lower() == 'vr':
            numerador = Z_R
        elif saida.lower() == 'vl':
            numerador = Z_L
        else:
            raise ValueError("A saída deve ser 'vc', 'vr' ou 'vl'.")

        self.funcao_transferencia = sp.simplify(numerador / Z_total)
        print(f"\n--- Função de Transferência H(s) = {saida.upper()}(s)/V_in(s) ---")
        sp.pprint(self.funcao_transferencia)
        print("----------------------------------------------------")
        return self.funcao_transferencia

    def resolver_edo(self, tipo_fonte, V_amplitude=1.0, freq_fonte=0, t_final=10, pontos=1000, cond_iniciais=(0,0)):
        """
        Resolve a EDO numericamente usando scipy.integrate.odeint.

        Args:
            tipo_fonte (str): 'degrau' para CC ou 'senoidal' para CA.
            V_amplitude (float): Amplitude da fonte de tensão.
            freq_fonte (float): Frequência da fonte para o caso CA (em Hz).
            t_final (float): Tempo final da simulação.
            pontos (int): Número de pontos na simulação.
            cond_iniciais (tuple): (q(0), i(0)) -> (carga inicial, corrente inicial).
        """
        # A EDO de 2ª ordem precisa ser convertida em um sistema de duas EDOs de 1ª ordem.
        # Seja x1 = q(t) e x2 = q'(t) = i(t).
        # Então x1' = x2
        # E x2' = q''(t) = (1/L) * [v_in(t) - R*x2 - (1/C)*x1]

        # Define a função da fonte de tensão
        if tipo_fonte.lower() == 'degrau':
            v_in_func = lambda t: V_amplitude if t >= 0 else 0
            self.nome = f"RLC Série - Resposta ao Degrau CC ({V_amplitude}V)"
        elif tipo_fonte.lower() == 'senoidal':
            omega = 2 * np.pi * freq_fonte
            v_in_func = lambda t: V_amplitude * np.sin(omega * t)
            self.nome = f"RLC Série - Resposta Senoidal CA ({V_amplitude}V, {freq_fonte}Hz)"
        else:
            raise ValueError("Tipo de fonte deve ser 'degrau' ou 'senoidal'.")

        def sistema_edos(x, t, R, L, C, v_func):
            x1, x2 = x # x1 = q, x2 = i
            v_t = v_func(t)
            dx1_dt = x2
            dx2_dt = (1/L) * (v_t - R*x2 - (1/C)*x1)
            return [dx1_dt, dx2_dt]

        # Vetor de tempo
        t_vetor = np.linspace(0, t_final, pontos)

        # Solução numérica
        print("\nIniciando a solução numérica da EDO...")
        solucao = odeint(sistema_edos, cond_iniciais, t_vetor, args=(self.R, self.L, self.C, v_in_func))
        print("Solução numérica concluída.")

        # Extraindo resultados
        q_t = solucao[:, 0]
        i_t = solucao[:, 1]
        v_in_t = np.array([v_in_func(t_i) for t_i in t_vetor])
        
        # Calculando tensões nos componentes
        # Vc(t) = q(t)/C
        # Vr(t) = R * i(t)
        # Vl(t) = v_in(t) - Vr(t) - Vc(t)
        v_c_t = q_t / self.C
        v_r_t = self.R * i_t
        v_l_t = v_in_t - v_r_t - v_c_t
        

        self.resultados_simulacao = {
            'Tempo (s)': t_vetor,
            'Tensão de Entrada (V)': v_in_t,
            'Corrente i(t) (A)': i_t,
            'Tensão no Capacitor Vc(t) (V)': v_c_t,
            'Tensão no Resistor Vr(t) (V)': v_r_t,
            'Tensão no Indutor Vl(t) (V)': v_l_t
        }

# =============================================================================
# Exemplo de Uso do Framework
# =============================================================================
if __name__ == '__main__':

    # --- EXEMPLO 1: Circuito RLC subamortecido com fonte CC (Resposta ao Degrau) ---
    print("="*60)
    print("EXEMPLO 1: Análise de Circuito RLC com Fonte CC (Subamortecido)")
    print("="*60)

    # 1. Instanciar o circuito com seus componentes
    # Valores para um sistema subamortecido: R < 2*sqrt(L/C)
    circuito_cc = CircuitoRlcSerie(R=10, L=0.5, C=100e-6)
    circuito_cc.exibir_componentes()

    # 2. Obter a função de transferência simbólica (ex: tensão no capacitor)
    circuito_cc.obter_funcao_transferencia(saida='vc')

    # 3. Resolver a EDO para uma fonte degrau de 10V
    # Condições iniciais: capacitor descarregado (q(0)=0) e sem corrente inicial (i(0)=0)
    circuito_cc.resolver_edo(
        tipo_fonte='degrau',
        V_amplitude=10.0,
        t_final=1.5,
        cond_iniciais=(0, 0) # (q(0), i(0))
    )

    # 4. Visualizar os resultados em um gráfico
    circuito_cc.plotar_resultados()

    # 5. Exportar resultados para um DataFrame Pandas
    df_cc = circuito_cc.resultados_to_dataframe()
    print("\n--- Primeiras 5 linhas do DataFrame (Exemplo CC) ---")
    print(df_cc.head())
    print("-" * 50)


    # --- EXEMPLO 2: Circuito RLC com fonte CA ---
    print("\n" + "="*60)
    print("EXEMPLO 2: Análise de Circuito RLC com Fonte CA")
    print("="*60)

    # 1. Instanciar o circuito
    circuito_ca = CircuitoRlcSerie(R=50, L=0.1, C=20e-6)
    circuito_ca.exibir_componentes()
    
    # 2. Obter a função de transferência (ex: tensão no resistor)
    circuito_ca.obter_funcao_transferencia(saida='vr')

    # 3. Resolver a EDO para uma fonte senoidal
    circuito_ca.resolver_edo(
        tipo_fonte='senoidal',
        V_amplitude=10.0,
        freq_fonte=60, # 60 Hz
        t_final=0.2,
        pontos=2000
    )

    # 4. Plotar os resultados
    circuito_ca.plotar_resultados()
    
    # 5. Obter o dataframe
    df_ca = circuito_ca.resultados_to_dataframe()
    print("\n--- Primeiras 5 linhas do DataFrame (Exemplo CA) ---")
    print(df_ca.head())
    print("-" * 50)

