import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class CalculadoraFoguete:
    """
    Uma classe para calcular o tempo em que um foguetão atinge uma
    determinada velocidade, usando o Método da Secante.
    """
    def __init__(self, u, m0, q, g, v_alvo):
        """
        Inicializa a calculadora com os parâmetros do foguetão.

        Args:
            u (float): Velocidade de exaustão do combustível (m/s).
            m0 (float): Massa inicial do foguetão (Kg).
            q (float): Taxa de consumo de combustível (Kg/s).
            g (float): Aceleração da gravidade (m/s^2).
            v_alvo (float): Velocidade que se pretende atingir (m/s).
        """
        self.u = u
        self.m0 = m0
        self.q = q
        self.g = g
        self.v_alvo = v_alvo
        
        # Define a variável simbólica 't' para o tempo
        self.t_simbolico = sp.symbols('t')
        
        # Define a função f(t) = 0 de forma simbólica com SymPy
        # f(t) = u * ln(m0 / (m0 - q*t)) - g*t - v_alvo
        self.funcao_simbolica = (self.u * sp.log(self.m0 / (self.m0 - self.q * self.t_simbolico)) 
                               - self.g * self.t_simbolico 
                               - self.v_alvo)
        
        # Converte a função simbólica para uma função numérica para cálculos rápidos
        self.funcao_numerica = sp.lambdify(self.t_simbolico, self.funcao_simbolica, 'numpy')
        
        self.iteracoes_df = None
        self.solucao = None
        self.num_iter_realizadas = 0

    def metodo_da_secante(self, t0, t1, e1=1e-2, e2=1e-1, max_iter=3):
        """
        Aplica o método da secante para encontrar a raiz da equação.

        Args:
            t0 (float): Primeira estimativa inicial para o tempo.
            t1 (float): Segunda estimativa inicial para o tempo.
            e1 (float): Tolerância para o critério de paragem relativo.
            e2 (float): Tolerância para o critério de paragem do valor da função.
            max_iter (int): Número máximo de iterações.

        Returns:
            float: O tempo 't' calculado.
        """
        historico_iteracoes = []
        tk_minus_1, tk = t0, t1

        for i in range(max_iter):
            self.num_iter_realizadas = i + 1
            ftk_minus_1 = self.funcao_numerica(tk_minus_1)
            ftk = self.funcao_numerica(tk)
            
            # Garante que não há divisão por zero
            if abs(ftk - ftk_minus_1) < 1e-15:
                print("Diferença entre f(t_k) e f(t_k-1) muito pequena. Parando.")
                break

            # Fórmula do Método da Secante
            tk_plus_1 = tk - (ftk * (tk - tk_minus_1)) / (ftk - ftk_minus_1)
            ftk_plus_1 = self.funcao_numerica(tk_plus_1)
            
            erro_relativo = np.abs((tk_plus_1 - tk) / tk_plus_1) if tk_plus_1 != 0 else 0
            
            historico_iteracoes.append({
                'Iteração': i + 1,
                't_k-1': tk_minus_1,
                't_k': tk,
                'f(t_k)': ftk,
                't_k+1 (Solução)': tk_plus_1,
                '|f(t_k+1)|': np.abs(ftk_plus_1),
                'Erro Relativo': erro_relativo
            })
            
            # Atualiza os valores para a próxima iteração
            tk_minus_1, tk = tk, tk_plus_1
            
            # Verifica os critérios de paragem
            if erro_relativo < e1 and np.abs(ftk_plus_1) < e2:
                print(f"\nCritérios de paragem atingidos na iteração {self.num_iter_realizadas}.")
                break
        
        self.solucao = tk
        self.iteracoes_df = pd.DataFrame(historico_iteracoes)
        return self.solucao

    def exibir_resultados(self):
        """
        Exibe os resultados das iterações e a solução final.
        """
        if self.iteracoes_df is None:
            print("Execute o método da secante primeiro.")
            return
            
        print("--- Tabela de Iterações (Método da Secante para o Foguetão) ---")
        print(self.iteracoes_df.to_string())
        print(f"\nNúmero de iterações realizadas: {self.num_iter_realizadas}")
        print("\n" + "="*50 + "\n")
        
        print(f"Solução Final (tempo t): {self.solucao:.6f} segundos")
        print(f"Valor da função no ponto final f(t): {self.funcao_numerica(self.solucao):.6f}")

    def plotar_grafico(self, t_min, t_max):
        """
        Plota o gráfico da função e a raiz encontrada.
        """
        if self.solucao is None:
            print("Execute o método da secante para encontrar a solução a ser plotada.")
            return

        t_vals = np.linspace(t_min, t_max, 400)
        f_vals = self.funcao_numerica(t_vals)

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(t_vals, f_vals, label='$f(t) = u \\ln(\\frac{m_0}{m_0 - qt}) - gt - v_{alvo}$', color='crimson')
        ax.axhline(0, color='black', linestyle='--', linewidth=0.7)
        ax.plot(self.solucao, self.funcao_numerica(self.solucao), 'ko', markersize=8, label=f'Solução encontrada t ≈ {self.solucao:.4f}s')

        ax.set_xlabel('Tempo (t) em segundos')
        ax.set_ylabel('Valor da Função f(t)')
        ax.set_title('Velocidade do Foguetão: Encontrando o Tempo t para v = 1000 m/s')
        ax.legend(fontsize=12)
        ax.grid(True)
        
        ax.annotate('Raiz (f(t)=0)', 
                    xy=(self.solucao, 0), 
                    xytext=(self.solucao - 5, 100),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))
                    
        plt.show()

# --- Execução do Programa ---
if __name__ == "__main__":
    # Parâmetros do problema do foguetão
    u_foguete = 2200       # m/s
    m0_foguete = 1.6e5     # Kg
    q_foguete = 2680       # Kg/s
    g_foguete = 9.8        # m/s^2
    v_alvo_foguete = 1000  # m/s
    
    # Valores iniciais e critérios de paragem
    t0_inicial = 20
    t1_inicial = 30
    e1_tol = 1e-2
    e2_tol = 1e-1
    max_iteracoes = 3

    # Cria a instância da calculadora
    calculadora = CalculadoraFoguete(u=u_foguete, m0=m0_foguete, q=q_foguete, g=g_foguete, v_alvo=v_alvo_foguete)
    
    # Executa o método e exibe os resultados
    calculadora.metodo_da_secante(t0=t0_inicial, t1=t1_inicial, e1=e1_tol, e2=e2_tol, max_iter=max_iteracoes)
    calculadora.exibir_resultados()
    
    # Plota o gráfico
    calculadora.plotar_grafico(t_min=20, t_max=30)
