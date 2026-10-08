---
title: Campo Elétrico vs. Campo Magnético
description: 'Diferenças fundamentais, origens e as Equações de Maxwell associadas.'
date: '2026-04-24T19:00:00.000Z'
category: Física e Ciencias da Natureza
tags: ['Eletromagnetismo', 'Física', 'LaTeX']
draft: false
---

# Campo Elétrico vs. Campo Magnético: O Coração do Eletromagnetismo

Para quem estuda Engenharia Elétrica, entender a dualidade e as diferenças entre o Campo Elétrico ($\vec{E}$) e o Campo Magnético ($\vec{B}$) é o primeiro passo para dominar máquinas elétricas, transformadores e propagação de ondas.

## 1. Origens e Natureza

A diferença fundamental reside no estado de movimento das cargas:

* **Campo Elétrico ($\vec{E}$):** É gerado por **cargas elétricas**, estejam elas paradas ou em movimento. Uma carga pontual $q$ cria um campo que diverge radialmente.
* **Campo Magnético ($\vec{B}$):** É gerado apenas por **cargas em movimento** (correntes elétricas) ou por campos elétricos variantes no tempo.

## 2. A Força de Lorentz

A interação de uma carga com ambos os campos é unificada pela **Força de Lorentz**:

$$\vec{F} = q(\vec{E} + \vec{v} \times \vec{B})$$

Onde:
* $q\vec{E}$ é a força elétrica, que atua na mesma direção do campo.
* $q(\vec{v} \times \vec{B})$ é a força magnética, que é sempre **perpendicular** tanto à velocidade $\vec{v}$ quanto ao campo $\vec{B}$.

## 3. Linhas de Campo e Monopolos

Uma diferença visual e física crucial:
* As linhas de campo elétrico podem começar em cargas positivas e terminar em cargas negativas. Existem **monopolos elétricos**.
* As linhas de campo magnético são sempre loops fechados. **Não existem monopolos magnéticos** (até onde a ciência sabe). Se você quebrar um ímã ao meio, terá dois novos ímãs com Norte e Sul.

## 4. Equações de Maxwell (Estáticas)

As duas primeiras equações de Maxwell descrevem essa divergência de comportamento:

**Lei de Gauss (Eletricidade):**
$$\nabla \cdot \vec{E} = \frac{\rho}{\varepsilon_0}$$
*(O campo elétrico "nasce" ou "morre" onde há densidade de carga $\rho$)*

**Lei de Gauss para o Magnetismo:**
$$\nabla \cdot \vec{B} = 0$$
*(O fluxo magnético líquido através de uma superfície fechada é sempre zero, reforçando a inexistência de monopolos)*

---

*Estudo em andamento para a disciplina de Eletromagnetismo da UFF e suporte operacional na ONS.*
