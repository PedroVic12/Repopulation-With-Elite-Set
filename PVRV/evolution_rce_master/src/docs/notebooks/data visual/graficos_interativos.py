# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 14:12:01 2021

@author: Samaung
"""
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

fig = plt.figure()
gráfico = fig.add_subplot(111)

start = time.time()

xs = []
ys = []


def atualiza(i):
    dados = open(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/dados_texto.txt",
        "r",
    ).read()
    linhas = dados.split("\n")
    for y in linhas:
        if len(y) > 0:
            ys.append(float(y))
            if len(xs) == 0:
                xs.append(time.time() - start)
            if len(ys) > len(xs):
                x = time.time() - start
                xs.append(x)
    gráfico.clear()
    gráfico.plot(xs, ys, "-o")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Valor digitado")
    plt.title("Valor digitado em função do tempo")
    ys.clear()


a = animation.FuncAnimation(fig, atualiza, interval=1)
plt.show()
