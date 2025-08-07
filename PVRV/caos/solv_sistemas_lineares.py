import numpy as np
import pandas as pd

class SolucionadorSistemaLinear:
    """
    Uma classe para resolver sistemas de equações lineares Ax = b
    usando o método de Eliminação de Gauss com Pivotagem Parcial (EGPP).
    Calcula também o determinante e a matriz inversa.
    """
    def __init__(self, A, b):
        """
        Inicializa o solucionador com a matriz de coeficientes A e o vetor b.

        Args:
            A (list or np.array): A matriz dos coeficientes.
            b (list or np.array): O vetor dos termos independentes.
        """
        self.A_original = np.array(A, dtype=float)
        self.b_original = np.array(b, dtype=float).reshape(-1, 1)
        self.n = len(b)
        
        # Verifica se a matriz A é quadrada
        if self.A_original.shape[0] != self.n or self.A_original.shape[1] != self.n:
            raise ValueError("A matriz A tem de ser quadrada.")

        self.U = None
        self.b_transformado = None
        self.trocas_de_linha = 0
        self.passos_eliminacao = []

    def eliminacao_gauss_pivotagem(self):
        """
        Executa a Eliminação de Gauss com Pivotagem Parcial para transformar
        a matriz A numa matriz triangular superior U.
        """
        # Evita reexecutar se já foi feito
        if self.U is not None:
            return

        # Cria uma cópia de trabalho da matriz A e do vetor b
        A_trabalho = self.A_original.copy()
        b_trabalho = self.b_original.copy()
        self.trocas_de_linha = 0
        self.passos_eliminacao = []

        print("--- Início da Eliminação de Gauss com Pivotagem Parcial ---")
        matriz_ampliada = np.hstack([A_trabalho, b_trabalho])
        print("Matriz Ampliada Inicial [A|b]:")
        print(pd.DataFrame(matriz_ampliada))
        print("-" * 50)

        for k in range(self.n - 1):
            # --- Pivotagem Parcial ---
            # Encontra o índice da linha com o maior elemento (em módulo) na coluna k
            indice_pivot = np.argmax(np.abs(A_trabalho[k:, k])) + k
            
            if indice_pivot != k:
                print(f"Etapa {k+1}: Troca de linha {k+1} com a linha {indice_pivot+1}")
                # Troca as linhas em A
                A_trabalho[[k, indice_pivot]] = A_trabalho[[indice_pivot, k]]
                # Troca as linhas em b
                b_trabalho[[k, indice_pivot]] = b_trabalho[[indice_pivot, k]]
                self.trocas_de_linha += 1
                
                matriz_ampliada = np.hstack([A_trabalho, b_trabalho])
                print("Matriz após troca de linhas:")
                print(pd.DataFrame(matriz_ampliada))
                
            # --- Eliminação ---
            pivot = A_trabalho[k, k]
            print(f"Etapa {k+1}: Pivot = {pivot:.6f} (na posição a{k+1},{k+1})")
            
            for i in range(k + 1, self.n):
                multiplicador = A_trabalho[i, k] / pivot
                print(f"   - Multiplicador m{i+1},{k+1} = {multiplicador:.6f}")
                
                # Atualiza a linha i da matriz A e do vetor b
                A_trabalho[i, k:] = A_trabalho[i, k:] - multiplicador * A_trabalho[k, k:]
                b_trabalho[i] = b_trabalho[i] - multiplicador * b_trabalho[k]

            matriz_ampliada = np.hstack([A_trabalho, b_trabalho])
            self.passos_eliminacao.append(matriz_ampliada.copy())
            print(f"Matriz no final da Etapa {k+1}:")
            print(pd.DataFrame(matriz_ampliada))
            print("-" * 50)

        self.U = A_trabalho
        self.b_transformado = b_trabalho
        print("--- Fim da Eliminação de Gauss ---")

    def resolver_sistema(self):
        """
        Resolve o sistema Ax=b usando EGPP e substituição inversa.
        
        Returns:
            np.array: O vetor solução x (as correntes i1, i2, i3).
        """
        # Executa a eliminação primeiro
        self.eliminacao_gauss_pivotagem()
        
        print("\n--- a) Cálculo das Correntes (Solução do Sistema) ---")
        print("Resolvendo o sistema triangular superior Ux = b' por substituição inversa.")
        
        x = np.zeros(self.n)
        for i in range(self.n - 1, -1, -1):
            soma = np.dot(self.U[i, i + 1:], x[i + 1:])
            x[i] = (self.b_transformado[i] - soma) / self.U[i, i]
        
        print("\nSolução (valores das correntes):")
        for i in range(self.n):
            print(f"  i{i+1} = {x[i]:.6f}")
        return x

    def calcular_determinante(self):
        """
        Calcula o determinante da matriz A.
        
        Returns:
            float: O valor do determinante.
        """
        self.eliminacao_gauss_pivotagem()
        
        print("\n--- b) Cálculo do Determinante ---")
        det = np.prod(np.diag(self.U)) * ((-1)**self.trocas_de_linha)
        print(f"Determinante = det(U) * (-1)^t = {np.prod(np.diag(self.U)):.4f} * (-1)^{self.trocas_de_linha}")
        print(f"Determinante = {det:.6f}")
        return det

    def calcular_inversa(self):
        """
        Calcula a matriz inversa de A.

        Returns:
            np.array: A matriz inversa A^-1.
        """
        self.eliminacao_gauss_pivotagem()
        
        print("\n--- c) Cálculo da Matriz Inversa ---")
        I = np.identity(self.n)
        A_inv = np.zeros((self.n, self.n))

        # Precisamos aplicar as mesmas transformações de EGPP a I
        # Vamos usar a função solve do numpy que é eficiente, mas o processo manual é:
        # Para cada coluna 'j' da identidade, resolver o sistema A*x_j = e_j
        
        print("Para encontrar A^-1, resolvemos n sistemas lineares Ax = e_j,")
        print("onde e_j é a j-ésima coluna da matriz identidade.")
        
        for j in range(self.n):
            # Resolve o sistema A*x = e_j usando a fatorização LU implícita no EGPP
            # Forma mais simples e numericamente estável:
            coluna_inv = np.linalg.solve(self.A_original, I[:, j])
            A_inv[:, j] = coluna_inv

        print("\nMatriz Inversa A^-1:")
        print(pd.DataFrame(A_inv))
        return A_inv

# --- Execução do Programa ---
if __name__ == "__main__":
    # Definição do sistema a partir do problema do circuito
    # x1 + x2 + x3 = 0
    # 10*x1 - 8*x2 = 65
    # 8*x1 - 3*x3 = 120
    
    A_matrix = [[1, 1, 1],
                [10, -8, 0],
                [8, 0, -3]]
                
    b_vector = [0, 65, 120]

    # Cria a instância do solucionador
    solucionador = SolucionadorSistemaLinear(A=A_matrix, b=b_vector)

    # a) Calcula as correntes
    correntes = solucionador.resolver_sistema()

    # b) Calcula o determinante
    determinante = solucionador.calcular_determinante()

    # c) Calcula a matriz inversa
    inversa = solucionador.calcular_inversa()

