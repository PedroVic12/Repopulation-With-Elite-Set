---
title: roteiro blog 2026
description: 'Planejamento e estratégia para a criação de novos posts técnicos no blog'
date: '2026-04-24T18:54:54.000Z'
category: EStudos e Produtividade
tags: ['Astro', 'LaTeX', 'Engenharia Elétrica', 'Python']
draft: false
---

# Roteiro Blog 2026: Consolidação do Conhecimento

Este documento detalha a estratégia de uso do blog Astro (integrado ao Obsidian) como a principal ferramenta de estudos e construção de portfólio. O objetivo é criar conteúdos de alto nível em Engenharia Elétrica, Física e Programação, utilizando Markdown avançado, fórmulas matemáticas (LaTeX) e scripts interativos.

## 1. Nova Estratégia de Estudos (2026)

A "Batcaverna" (Obsidian + Astro) agora funciona como um pipeline de publicação contínua. 
* **Markdown como Base:** Todas as anotações brutas nascem no Obsidian.
* **LaTeX para Rigor Matemático:** Uso das tags `$` e `$$` para renderizar equações diferenciais, matrizes Y-Bus e Leis de Maxwell com perfeição acadêmica.
* **Código Interativo:** Inclusão de blocos de código em Python (Sympy, Pandas, Matplotlib) que não apenas explicam a teoria, mas mostram a aplicação prática (ex: Otimização AG, simulações no PandaPower).
* **Ingestão Automática:** O script `ingest-pvrv.mjs` puxa o conteúdo da pasta `Jedi-CyberPunk/PVRV` e o converte em páginas estáticas no Astro.

---

## 2. Roteiro dos Próximos Posts Técnicos

Para testar a nova arquitetura e consolidar a base teórica para a ONS e UFF, os seguintes posts serão criados e publicados na plataforma:

### Post 1: Campo Elétrico vs. Campo Magnético
* **Objetivo:** Diferenciar as origens e os efeitos desses dois campos fundamentais do eletromagnetismo.
* **Conteúdo Planejado:**
  * **Origens:** Cargas em repouso (geram campo elétrico $\vec{E}$) versus cargas em movimento/corrente (geram campo magnético $\vec{B}$).
  * **As Forças:** A Força de Lorentz ($\vec{F} = q(\vec{E} + \vec{v} \times \vec{B})$) formatada em LaTeX.
  * **Linhas de Campo:** Como as linhas de $\vec{E}$ divergem/convergem e as de $\vec{B}$ são sempre contínuas (inexistência de monopolos magnéticos).
  * **Equações de Maxwell (Forma Diferencial):**
    * Lei de Gauss: $\nabla \cdot \vec{E} = \frac{\rho}{\varepsilon_0}$
    * Lei de Gauss para o Magnetismo: $\nabla \cdot \vec{B} = 0$

### Post 2: A Dança do Inverso do Quadrado: Força Elétrica vs. Força Gravitacional
* **Objetivo:** Traçar um paralelo entre a Lei de Coulomb e a Lei da Gravitação Universal de Newton, demonstrando a similaridade estrutural e a colossal diferença de magnitude.
* **Conteúdo Planejado:**
  * **As Fórmulas (LaTeX):**
    * Gravitação: $F_g = G \frac{m_1 m_2}{r^2}$
    * Coulomb: $F_e = k_e \frac{|q_1 q_2|}{r^2}$
  * **A Matemática:** Por que ambas obedecem à lei do inverso do quadrado da distância ($1/r^2$). A diferença fundamental (gravidade só atrai, eletricidade atrai e repele).
  * **As Constantes:** O choque de realidade entre $G$ ($10^{-11}$) e $k_e$ ($10^9$).
  * **Mão na Massa (Python):**
    * Bloco de código usando `sympy` para manipulação algébrica das equações.
    * Bloco de código usando `matplotlib` para plotar a curva de decaimento de $1/r^2$ demonstrando como a força despenca ao afastar as partículas/massas.

### Post 3: Introdução a Sistemas Elétricos de Potência (SEP) - O Triângulo de Potências
* **Objetivo:** Explicar de forma didática os conceitos que governam o fluxo de energia no Sistema Interligado Nacional (SIN), essencial para o trabalho na ONS.
* **Conteúdo Planejado:**
  * **O que é Potência Ativa (P):** A energia que realiza trabalho útil (Watts). Fórmulas: $P = V I \cos(\theta)$.
  * **O que é Potência Reativa (Q):** A energia que vai e volta, usada para magnetizar motores e transformadores (VAr). Essencial para o controle de tensão na ONS. Fórmulas: $Q = V I \sin(\theta)$.
  * **A Potência Aparente (S):** A soma vetorial das duas, o que o sistema realmente precisa suportar (VA). Fórmula: $S = V I^*$, ou $S = \sqrt{P^2 + Q^2}$.
  * **O Fator de Potência:** O famoso $\cos(\theta)$ e por que a ONS e as concessionárias exigem que ele fique próximo de 1.
  * **Visualização:** Uso de LaTeX para desenhar as relações trigonométricas.