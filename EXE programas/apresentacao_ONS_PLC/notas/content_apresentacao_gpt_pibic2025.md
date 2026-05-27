# Aplicando estratégias de diversificação em algoritmos evolutivos para problemas de Otimização em Engenharia Elétrica

Autor: Pedro Victor Rodrigues Veras
Prof. Orientador: Rainer Zanghi
Departamento de Engenharia Elétrica / Escola de Engenharia / LMSE
Universidade Federal Fluminense (UFF)  Programa de Iniciação Científica (PIBIC)

---

## Sumário

1) Introdução
2) Metodologia
3) Fundamentação Teórica
4) Arquitetura do Software
5) Resultados
6) Conclusões

---

## MOTIVAÇÃO

Esta pesquisa científica utiliza modelagem matemática e meta-heurísticas baseadas em processos bioinspirados, como a seleção natural, usando apenas a linguagem de programação Python para otimizar o agendamento de intervenções e operações em Sistemas Elétricos de Potência (SEP). O Software utiliza algoritmos evolutivos com DEAP e análise de contingências com Pandapower. O projeto é de código aberto e busca colaboradores para sua documentação online.

## Repositorio no Github

- **Repopulation-With-Elite-Set (UFF)**

---

## Metodologia em 4 etapas

1) Estudo Bibliográfico do caso de Agendamento Ótimo no SEP

- Revisão de conceitos fundamentais para anaĺise de Sistemas Elétricos de Potência (SEP) com algoritmos evolutivos e Pandapower

1) Elaboração de um novo algoritimo de otimização usando Algoritimo Evolutivo

- Definição de váriaveis de decisão, restrições e função objetivo do problema

1) Implementação do código em Python e Simulações de cenários

- Uso apenas da linguagem Python usando as bibliotecas: DEAP, Pandas, PandaPower e Pyside6

1) Testes de validação

- Testes de otimização em Redes IEEE 14, 30, 118 e SIN 45

---

## Slide 1 — Capa

Aplicando estratégias de diversificação em algoritmos evolutivos para problemas de Otimização em Engenharia Elétrica

### Linha de Pesquisa

- Sistemas Elétricos de Potência (SEP)
- Metaheurísticas
- Algoritmos Evolutivos
- Otimização de Agendamento
- Planejamento da Operação

### Tecnologias

- Python
- DEAP
- Pandapower
- Pandas
- PySide6
- Streamlit

### Legenda da imagem

**Figura 1 — Arquitetura geral do framework de otimização aplicado ao SEP.**

> Inserir imagem:

- Fluxograma do framework
- AG + Pandapower + Dashboard
- Arquitetura do sistema

---

## Slide 2 — Motivação

## Contexto Operativo

- O Sistema Interligado Nacional (SIN) possui alta complexidade operacional.
- Desligamentos programados alteram a topologia da rede.
- Contingências simultâneas podem gerar:

  - Sobrecargas
  - Colapso de tensão
  - Corte de carga
  - Ilhamento

## Problema

O operador precisa:

- Minimizar riscos operativos
- Atender restrições elétricas
- Respeitar prioridades de manutenção
- Garantir segurança operativa

## Desafio Computacional

O problema possui:

- Espaço combinatório explosivo
- Alta epistasia
- Função objetivo não linear
- Alto custo computacional

Legenda da imagem

**Figura 2 — Exemplo de múltiplos cenários operativos no agendamento de intervenções.**

> Inserir imagem:

- Figura 4.3 da tese de doutorado
- Cenários operativos

---

## Slide 3 — Fundamentação Teórica

## Metaheurísticas e Algoritmos Evolutivos

- Processo Estocatico, problema classico de programação linear para otimização

## Algoritmos Genéticos

Inspirados em:

- Seleção natural
- Mutação
- Cruzamento
- Evolução populacional

## Estratégia RCE

### Repopulation-With-Elite-Set

Objetivos:

- Evitar convergência prematura
- Preservar diversidade
- Melhorar exploração do espaço de busca
- Intensificar regiões promissoras

## Conceitos importantes

- Epistasia
- Diversificação
- Intensificação
- Conjunto Elite
- Critério de Unicidade

 Legenda da imagem

**Figura 3 — Migração de indivíduos do conjunto elite durante repopulações da estratégia RCE.**

> Inserir imagem:

- Figura 4.6 da tese de doutorado

---

## Slide 4 — Formulação Matemática

## Modelagem Matemática para o algoritmo de otimização

## Variáveis de decisão

Cada gene representa:

- Horário inicial de desligamento
- Duração da intervenção
- Cenário operativo

## Função Objetivo

Minimizar:

[
Fitness = \sum_{cenários} \left(
w_v V_{violação}
+
w_f F_{violação}
+
w_c C_{corte}
\right)
]

Onde:

- (V_{violação}) → violações de tensão
- (F_{violação}) → sobrecarga em linhas/transformadores
- (C_{corte}) → penalidade por não atendimento

## Restrições

- Limites operativos
- Segurança N-1
- Limites de tensão
- Limites térmicos
- Atendimento à demanda

 Legenda da imagem

**Figura 4 — Representação genética do cromossomo de agendamento.**

> Inserir imagem:

- Figura 4.4 da tese de doutorado

---

## Slide 5 — Arquitetura do Framework

## Framework de Otimização

## Estrutura Geral

### Núcleo Matemático

- DEAP
- Algoritmos Evolutivos
- Estratégia RCE

### Simulação Elétrica

- Pandapower
- Fluxo de potência AC
- Contingências N-k

### Interface Desktop

- PySide6 (Qt)

### Dashboard Analítico

- Streamlit

## Diferencial

O framework transforma:

### Pesquisa acadêmica → ferramenta operativa

 Legenda da imagem

**Figura 5 — Arquitetura modular do framework desenvolvido em Python.**

> Inserir imagem:

- Arquitetura própria do projeto
- Launcher + núcleo + dashboard

---

## Slide 6 — Classe RedeEletricaPandaPower

Classe RedeEletricaPandaPower

## Responsabilidades

- Carregamento da rede
- Simulação elétrica
- Avaliação de cenários
- Controle de contingências
- Cálculo de fitness

## Principais Métodos

| Método                       | Função                  |
| ---------------------------- | ----------------------- |
| carregar_redes_padrao()      | Carrega rede IEEE       |
| avalia_cenarios()            | Gera matriz de cenários |
| executar_fluxo_de_carga()    | Executa runpp           |
| calcular_violacoes_fitness() | Avalia violações        |
| hashtableindex()             | Evita recálculos        |

## Otimização Computacional

Uso de:

- Hashtable
- Paralelismo
- Cache de cenários

Legenda da imagem

**Figura 6 — Fluxo de execução da classe RedeEletricaPandaPower.**

> Inserir imagem:

- Fluxograma interno da classe

---

## Slide 7 — (OBS RAINER) Não Convergência do Fluxo

## Por que o fluxo não converge?

## Não convergência ≠ erro

É um comportamento esperado em cenários críticos.

## Possíveis causas

- Colapso de tensão
- Sobrecargas severas
- Instabilidade operacional
- Ilhamento elétrico

## Estratégia utilizada

O algoritmo:

- Penaliza cenários inviáveis
- Aumenta fitness do indivíduo
- Aprende regiões seguras da busca

## Resultado

O AG aprende automaticamente:

### quais combinações operativas devem ser evitadas

 Legenda da imagem

**Figura 7 — Exemplo de cenário não convergente em contingência N-k.**

> Inserir imagem:

- Fluxo divergente
- Colapso de tensão
- Curvas de tensão

---

## Slide 8 — Resultados

## Resultados Experimentais

## Sistemas testados

- IEEE 14
- IEEE 30
- IEEE 57
- IEEE 118
- SIN 45

## Resultados observados

- Redução de violações
- Melhor distribuição temporal
- Maior diversidade populacional
- Melhor convergência

## Ganhos computacionais

- Uso de Hashtable
- Paralelismo
- RCE

## Aplicabilidade

- Planejamento da operação
- Estudos de intervenção
- Apoio ao operador

 Legenda da imagem

**Figura 8 — Comparação entre agendamento solicitado e otimizado.**

> Inserir imagem:

- Tabelas 5.24 a 5.32
- Diagramas de tempo

---

## Slide 9 — Dashboard Streamlit

Dashboard Analítico

## Funcionalidades

- Evolução do fitness
- Melhor indivíduo
- Comparação entre execuções
- Estatísticas do AG
- Visualização operacional

## Benefícios

- Tomada de decisão rápida
- Análise visual
- Interação com resultados

 Legenda da imagem

**Figura 9 — Dashboard Streamlit para análise das execuções do algoritmo evolutivo.**

> Inserir imagem:

- Dashboard real do projeto

---

## Slide 10 — Trabalhos Futuros

Trabalhos Futuros

## Integrações

- Leitura de arquivos .pwf
- Integração com AnaRede
- Integração com Organon

## Inteligência Artificial

- Agentes inteligentes
- IA para apoio operacional
- Aprendizado por reforço

## Visualização Avançada

- Redes 3D
- Three.js
- Monitoramento em tempo real

## Pesquisa Científica

- Estabilidade transitória
- Métodos híbridos
- Sympy + Quarto.md
- EDOs em SEP

Legenda da imagem

**Figura 10 — Roadmap tecnológico do framework de otimização para aplicações futuras.**

> Inserir imagem:

- Roadmap visual
- Ecossistema tecnológico

---

## Slide 11 — Conclusões

## Conclusões

## O trabalho demonstrou que

- Algoritmos evolutivos são adequados para o problema de agendamento no SEP.
- A estratégia RCE melhora diversidade e qualidade das soluções.
- O Pandapower permite modelagem eficiente de redes elétricas.
- O framework possui potencial real de aplicação no ONS.

> Inserir imagem:

- SIN
- linhas de transmissão
- visualização energética do Brasil

## Contribuições Científicas

- Framework open source
- Integração otimização + SEP
- Ferramenta escalável
- Base para futuras pesquisas

## referencias

---

## Slide 12 — Fim

## Obrigado

Pedro Victor Rodrigues Veras
Engenharia Elétrica — UFF
