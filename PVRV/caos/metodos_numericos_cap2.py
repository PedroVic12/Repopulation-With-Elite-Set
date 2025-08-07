import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class CalculadoraEmprestimo:
    """
    Uma classe para calcular a taxa de juro de um empréstimo
    usando o Método da Secante e visualizar os resultados.
    """
    def __init__(self, C, M, n):
        """
        Inicializa a calculadora com os parâmetros do empréstimo.

        Args:
            C (float): Capital emprestado.
            M (float): Anuidade (pagamento anual).
            n (int): Número de anos.
        """
        self.C = C
        self.M = M
        self.n = n
        self.r_simbolico = sp.symbols('r')
        
        # Define a função f(r) = 0 de forma simbólica com SymPy
        self.funcao_simbolica = (self.M / self.r_simbolico) * (1 - (1 + self.r_simbolico)**-self.n) - self.C
        
        # Converte a função simbólica para uma função numérica para cálculos rápidos
        self.funcao_numerica = sp.lambdify(self.r_simbolico, self.funcao_simbolica, 'numpy')
        
        self.iteracoes_df = None
        self.solucao = None

    def metodo_da_secante(self, r0, r1, num_iteracoes=2):
        """
        Aplica o método da secante para encontrar a raiz da equação.

        Args:
            r0 (float): Primeira estimativa inicial.
            r1 (float): Segunda estimativa inicial.
            num_iteracoes (int): Número de iterações a serem realizadas.

        Returns:
            float: A taxa de juro calculada.
        """
        historico_iteracoes = []
        rk_minus_1, rk = r0, r1

        for i in range(num_iteracoes):
            frk_minus_1 = self.funcao_numerica(rk_minus_1)
            frk = self.funcao_numerica(rk)
            
            # Fórmula do Método da Secante
            rk_plus_1 = rk - (frk * (rk - rk_minus_1)) / (frk - frk_minus_1)
            
            historico_iteracoes.append({
                'Iteração': i + 1,
                'r_k-1': rk_minus_1,
                'r_k': rk,
                'f(r_k)': frk,
                'r_k+1 (Solução)': rk_plus_1
            })
            
            # Atualiza os valores para a próxima iteração
            rk_minus_1, rk = rk, rk_plus_1
            
        self.solucao = rk
        self.iteracoes_df = pd.DataFrame(historico_iteracoes)
        return self.solucao

    def exibir_resultados(self):
        """
        Exibe os resultados das iterações e a solução final.
        """
        if self.iteracoes_df is None:
            print("Execute o método da secante primeiro.")
            return
            
        print("--- Tabela de Iterações (Método da Secante) ---")
        print(self.iteracoes_df.to_string())
        print("\n" + "="*40 + "\n")
        
        # Calcula o erro relativo aproximado
        r_anterior = self.iteracoes_df.iloc[-1]['r_k']
        r_final = self.iteracoes_df.iloc[-1]['r_k+1 (Solução)']
        erro_relativo = np.abs((r_final - r_anterior) / r_final)
        
        print(f"Solução Final (taxa r): {self.solucao:.6f} ou {self.solucao:.2%}")
        print(f"Erro Relativo Aproximado: {erro_relativo:.2%}")

    def plotar_grafico(self, r_min=0.01, r_max=0.05):
        """
        Plota o gráfico da função e a raiz encontrada.
        """
        if self.solucao is None:
            print("Execute o método da secante primeiro para encontrar a solução a ser plotada.")
            return

        r_vals = np.linspace(r_min, r_max, 400)
        f_vals = self.funcao_numerica(r_vals)

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plota a função
        ax.plot(r_vals, f_vals, label=f'$f(r) = \\frac{{{self.M}}}{{r}}[1-(1+r)^{{-{self.n}}}] - {self.C}$', color='royalblue')
        
        # Linha do eixo x (f(r) = 0)
        ax.axhline(0, color='black', linestyle='--', linewidth=0.7)
        
        # Ponto da solução
        ax.plot(self.solucao, self.funcao_numerica(self.solucao), 'ro', label=f'Raiz encontrada r ≈ {self.solucao:.4f}')

        ax.set_xlabel('Taxa de Juro (r)')
        ax.set_ylabel('Valor da Função f(r)')
        ax.set_title('Visualização do Método da Secante')
        ax.legend()
        ax.grid(True)
        
        # Adiciona anotações
        ax.annotate('Raiz (f(r)=0)', 
                    xy=(self.solucao, 0), 
                    xytext=(self.solucao + 0.005, 500),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))

        plt.show()


# --- Execução do Programa ---
if __name__ == "__main__":
    # Parâmetros do problema
    C_emprestimo = 10000  # Capital
    M_anuidade = 1250    # Anuidade
    n_anos = 10          # Período
    
    # Valores iniciais para o método
    r0_inicial = 0.01
    r1_inicial = 0.05

    # Cria a instância da calculadora
    calculadora = CalculadoraEmprestimo(C=C_emprestimo, M=M_anuidade, n=n_anos)
    
    # Executa o método e exibe os resultados
    calculadora.metodo_da_secante(r0=r0_inicial, r1=r1_inicial, num_iteracoes=2)
    calculadora.exibir_resultados()
    
    # Plota o gráfico
    calculadora.plotar_grafico()
