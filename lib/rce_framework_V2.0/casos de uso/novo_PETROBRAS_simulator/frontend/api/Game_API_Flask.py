"""
Usaremos Flask, um micro framework web em Python, para criar uma API RESTful simples.

    Endpoints:
        /start: Comece o jogo e selecione o nível de dificuldade.
        /play: Gere e retorne um cálculo com base no nível de dificuldade.
        /check: Receba a resposta do jogador e verifique se está correta. Atualize e retorne o score.

"""

import sys
sys.path.append('../')

from backend.Game import Game
from flask import Flask, render_template, request, jsonify, session


app = Flask(__name__)
app.secret_key = 'some_secret_key'

@app.route('/')
def index():
    return render_template('index.html', question=None)

@app.route('/start', methods=['POST'])
def start():
    level = request.form.get('level')
    game = Game()
    question, answer = game.generate_calculation(level)
    session['score'] = 0  # resetando o score quando o jogo começa
    session['answer'] = answer
    return jsonify({'question': question, 'score': session['score'], 'level': level})

@app.route('/check', methods=['POST'])
def check():
    user_answer = int(request.form.get('answer'))
    correct = Game().check_answer(user_answer, session.get('answer'))
    if correct:
        session['score'] += 1
    return jsonify({'correct': correct, 'score': session['score']})

if __name__ == '__main__':
    app.run(debug=True)
