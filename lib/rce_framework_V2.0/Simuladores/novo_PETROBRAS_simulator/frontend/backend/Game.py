"""
Backend:
    Cálculo: Gere um cálculo com base no nível de dificuldade escolhido.
    Validação: Verifique se a resposta fornecida está correta.
    Score: Mantenha e atualize o score do jogador.
"""

import random
import operator

class Game:
    def __init__(self):
        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul
        }
        self.levels = {'easy': (1, 10), 'medium': (1, 100), 'hard': (1, 1000)}

    def generate_calculation(self, level):
        if level not in self.levels:
            raise ValueError(f"Nível {level} não é válido.")

        op_symbol = random.choice(list(self.operations.keys()))
        num1, num2 = random.randint(*self.levels[level]), random.randint(*self.levels[level])

        # Garante que não teremos operações de subtração que resultam em negativos.
        if op_symbol == '-' and num2 > num1:
            num1, num2 = num2, num1

        question = f"{num1} {op_symbol} {num2}"
        answer = self.operations[op_symbol](num1, num2)
        return question, answer

    def check_answer(self, user_answer, correct_answer):
        return user_answer == correct_answer
