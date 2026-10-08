# 🚀 Plano de Ação: Agile, XP, SOLID, Python e React

Bem-vindo ao seu plano de estudos e trabalho organizado! Use este documento como seu painel de controle pessoal. 

## 🧠 Como os conceitos se conectam:
- **Scrum**: Dá o ritmo (trabalhe em blocos de 1 a 2 semanas chamados *Sprints*) e estabelece rituais de planejamento e revisão.
- **Kanban**: Dá a visibilidade do fluxo da suaSprint, controlando o "Trabalho em Progresso" (WIP) para garantir que você não comece várias coisas sem terminá-las.
- **Extreme Programming (XP)**: Adiciona disciplina técnica (Testes TDD, Refatoração, Design Simples, Código Limpo).
- **SOLID**: Garante que o software que você está projetando não vai quebrar facialmente conforme ele cresce.

---

## 📊 Kanban da Iteração Atual (Sprint 1)

*Regra de Ouro do Kanban: Mova o `[x]` para indicar que algo foi concluído. Mantenha no máximo 2 itens no seu "Doing" (Fazendo) de cada vez.*

| To Do (Fazer) 📝 | Doing (Fazendo) ⏳ | Done (Feito) ✅ |
| :--- | :--- | :--- |
| Criar ambiente de desenvolvimento (Python + Node.js) | | |
| Estudar as regras do SCRUM (Eventos e Artefatos) | | |
| Ler sobre S.O.L.I.D em Python | | |
| Ler sobre S.O.L.I.D em React | | |


---

## 📋 Product Backlog (Sprints Planejadas)

Aqui estão as tarefas quebradas para o seu aprendizado e prática.

### 🏃‍♂️ Sprint 1: Fundamentos Ágeis e do S (Single Responsibility)
- [ ] **Teoria (Scrum/Kanban)**: Definir a duração da sua primeira Sprint (ex: 1 semana) e realizar a planning pessoal (escolher as tarefas do backlog).
- [ ] **XP**: Ler os princípios básicos do XP - principalmente **Test-Driven Development (TDD)** e **Simple Design**.
- [ ] **SOLID (Python)**: Criar uma classe simples que lê um arquivo CSV. Focar apenas no `S` (Single Responsibility Principle) e separar a função de leitura dos dados, da função de formatar/printar os dados.
- [ ] **SOLID (React)**: Pegar ou criar um Componente "gigante" (ex: um formulário com lógica embutida) e separar a camada de UI da Custom Hook (que conterá a lógica).

### 🏃‍♂️ Sprint 2: O & L (Open/Closed e Liskov Substitution) + XP TDD
- [ ] **XP / Ferramentas**: Instalar `pytest` no Python e configurar o `Jest` / `Testing Library` no React.
- [ ] **XP TDD**: Antes de escrever o código, escrever um teste que *falhe* testando uma pequena função ou componente. Depois escreva o código para *passar*. Em seguida, *refatore*. (Red -> Green -> Refactor).
- [ ] **SOLID (Python)**: Refatorar seu código da Sprint 1 aplicando o Open/Closed Principle utilizando `Abstract Base Classes` (`from abc import ABC`). Crie algo que seja fácil adicionar novos módulos sem mexer nas classes antigas.
- [ ] **SOLID (React)**: Aplicar Liskov na prática criando componentes que substituem componentes nativos do HTML (ex: criar um `<Button />` que aceita todos os atributos padrões de um `<button>` via props espalhadas usando `...props`).

### 🏃‍♂️ Sprint 3: I & D (Interface Segregation e Dependency Inversion)
- [ ] **XP**: Aplicar a prática de Integração Contínua (CI). Configurar Husky no repositório GitHub para bloquear *commits* se houver linting/tests quebrando.
- [ ] **SOLID (Python e React)**: Aplicar Dependency Inversion. No Python, injete dependências através do método `__init__`. No React, utilize inversão injetando métodos e dados via _Props_ e _Context API_, de modo que o componente de UI nunca busque dados primários da base de dados / API diretamente.
- [ ] **Scrum**: Fazer a sua primeira "Review" e "Retrospectiva" pessoal: O que deu certo? Como posso melhorar na próxima semana?

---
> **Dica XP**: Sempre que se deparar com um "Code Smell" (um código que parece estranho ou difícil de ler), pare e refatore. O código limpo não nasce de primeira.
