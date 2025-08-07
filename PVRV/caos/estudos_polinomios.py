import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class CalculadoraFissura:
    """
    Uma classe para encontrar o ponto onde a velocidade de propagação de uma
    fissura é nula, utilizando o Método da Secante na derivada da função de
    comprimento da fissura.
    """
    def __init__(self):
        """
        Inicializa a calculadora, define a função de comprimento e calcula sua derivada.
        """
        self.x_simbolico = sp.symbols('x')
        
        # Define a função de comprimento da fissura a(x)
        self.a_x = (2.02 * self.x_simbolico**5 - 1.28 * self.x_simbolico**4 + 
                    3.06 * self.x_simbolico**3 - 2.92 * self.x_simbolico**2 - 
                    5.66 * self.x_simbolico + 6.08)
        
        # A velocidade de propagação é a derivada a'(x). Esta é a nossa f(x).
        self.f_x = sp.diff(self.a_x, self.x_simbolico)
        
        print("--- Funções do Problema (Terminal) ---")
        print(f"Função de comprimento a(x): {self.a_x}")
        print(f"Função de velocidade f(x) = a'(x): {self.f_x}\n")
        
        # Converte as funções simbólicas para numéricas para cálculos e plots
        self.a_x_numerica = sp.lambdify(self.x_simbolico, self.a_x, 'numpy')
        self.funcao_numerica = sp.lambdify(self.x_simbolico, self.f_x, 'numpy')
        
        self.iteracoes_df = None
        self.solucao = None
        self.num_iter_realizadas = 0

    def metodo_da_secante(self, x0, x1, e1=1e-2, e2=1e-2, max_iter=3):
        """
        Aplica o método da secante para encontrar o zero da função f(x) = a'(x).

        Args:
            x0 (float): Primeira estimativa inicial.
            x1 (float): Segunda estimativa inicial.
            e1 (float): Tolerância para o critério de paragem relativo.
            e2 (float): Tolerância para o critério de paragem do valor da função.
            max_iter (int): Número máximo de iterações.

        Returns:
            float: O valor de 'x' calculado.
        """
        historico_iteracoes = []
        xk_minus_1, xk = x0, x1

        for i in range(max_iter):
            self.num_iter_realizadas = i + 1
            fxk_minus_1 = self.funcao_numerica(xk_minus_1)
            fxk = self.funcao_numerica(xk)
            
            if abs(fxk - fxk_minus_1) < 1e-15:
                print("Diferença entre f(x_k) e f(x_k-1) muito pequena. Parando.")
                break

            # Fórmula do Método da Secante
            xk_plus_1 = xk - (fxk * (xk - xk_minus_1)) / (fxk - fxk_minus_1)
            fxk_plus_1 = self.funcao_numerica(xk_plus_1)
            
            erro_relativo = np.abs((xk_plus_1 - xk) / xk_plus_1) if xk_plus_1 != 0 else 0
            
            historico_iteracoes.append({
                'Iteração': i + 1,
                'x_k-1': xk_minus_1,
                'x_k': xk,
                'f(x_k)': fxk,
                'x_k+1 (Solução)': xk_plus_1,
                '|f(x_k+1)|': np.abs(fxk_plus_1),
                'Erro Relativo': erro_relativo
            })
            
            xk_minus_1, xk = xk, xk_plus_1
            
            # Verifica os critérios de paragem
            if erro_relativo < e1 and np.abs(fxk_plus_1) < e2:
                print(f"\nCritérios de paragem atingidos na iteração {self.num_iter_realizadas}.")
                break
        
        self.solucao = xk
        self.iteracoes_df = pd.DataFrame(historico_iteracoes)
        return self.solucao

    def exibir_resultados(self):
        """
        Exibe os resultados das iterações e a solução final.
        """
        if self.iteracoes_df is None:
            print("Execute o método da secante primeiro.")
            return
            
        print("\n--- Tabela de Iterações (Terminal da Solução) ---")
        pd.options.display.float_format = '{:,.8f}'.format
        print(self.iteracoes_df.to_string())
        print(f"\nNúmero de iterações realizadas: {self.num_iter_realizadas}")
        print("\n" + "="*50 + "\n")
        
        print(f"Solução Final (fração de ciclos x): {self.solucao:.8f}")
        print(f"Velocidade de propagação no ponto f(x): {self.funcao_numerica(self.solucao):.8f}")

    def plotar_funcao_original(self, x_min, x_max):
        """
        Plota o gráfico da função original de comprimento da fissura, a(x).
        """
        x_vals = np.linspace(x_min, x_max, 400)
        a_vals = self.a_x_numerica(x_vals)

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(x_vals, a_vals, label="$a(x) = 2.02x^5 - ...$", color='royalblue')
        ax.axhline(0, color='black', linestyle='--', linewidth=0.7)
        
        ax.set_xlabel('Fração de ciclos (x)')
        ax.set_ylabel("Comprimento da Fissura a(x)")
        ax.set_title('Gráfico do Problema: Comprimento da Fissura vs. Ciclos')
        ax.legend(fontsize=12)
        ax.grid(True)
        
        plt.show()

    def plotar_grafico_solucao(self, x_min, x_max):
        """
        Plota o gráfico da função de velocidade a'(x) e a raiz encontrada.
        """
        if self.solucao is None:
            print("Execute o método da secante primeiro para encontrar a solução a ser plotada.")
            return

        x_vals = np.linspace(x_min, x_max, 400)
        f_vals = self.funcao_numerica(x_vals)

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(x_vals, f_vals, label="$f(x) = a'(x)$", color='darkorange')
        ax.axhline(0, color='black', linestyle='--', linewidth=0.7)
        ax.plot(self.solucao, self.funcao_numerica(self.solucao), 'bo', markersize=8, label=f'Solução encontrada x ≈ {self.solucao:.4f}')

        ax.set_xlabel('Fração de ciclos (x)')
        ax.set_ylabel("Velocidade de Propagação da Fissura a'(x)")
        ax.set_title('Gráfico da Solução: Velocidade Nula de Propagação da Fissura')
        ax.legend(fontsize=12)
        ax.grid(True)
        
        ax.annotate('Velocidade Nula (a\'(x)=0)', 
                    xy=(self.solucao, 0), 
                    xytext=(self.solucao - 0.1, -1),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))
                    
        plt.show()

# --- Execução do Programa ---
if __name__ == "__main__":
    # 1. Cria a instância da calculadora e mostra as equações no terminal
    calculadora = CalculadoraFissura()
    
    # 2. Mostra o gráfico do problema (função original a(x))
    calculadora.plotar_funcao_original(x_min=-1.0, x_max=1.5)

    # --- Início da Solução ---
    # Parâmetros para encontrar a raiz de a'(x) = 0
    x0_inicial = 0.8
    x1_inicial = 1.0
    
    # Critérios de paragem
    e1_tol = 1e-2
    e2_tol = 1e-2
    max_iteracoes = 3
    
    # 3. Executa o método para encontrar a solução e mostra os resultados no terminal
    calculadora.metodo_da_secante(x0=x0_inicial, x1=x1_inicial, e1=e1_tol, e2=e2_tol, max_iter=max_iteracoes)
    calculadora.exibir_resultados()
    
    # 4. Mostra o gráfico da solução (função a'(x) com a raiz encontrada)
    calculadora.plotar_grafico_solucao(x_min=0.7, x_max=1.1)

    
