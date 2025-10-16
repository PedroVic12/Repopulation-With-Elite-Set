# Exemplo de Execução: `run_AG_exemplo.py`

Este script é um exemplo prático, um "cliente" ou "driver", que demonstra como utilizar o framework `AlgoritimoEvolutivoRCE` para resolver um problema de otimização específico. Ele ilustra a simplicidade de uso do framework quando as classes principais (`Setup`, `AlgoritimoEvolutivoRCE`) já estão construídas.

## Estrutura do Script

O código abaixo segue um fluxo lógico que reflete os princípios da Programação Orientada a Objetos para configurar e executar um experimento.

```python
# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup, params, load_params
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE


#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, get_hash_table_size, consultaHashTable


# Variáveis de configuração
config_num = 1
params_base = load_params(f"params.json")
options = load_params(f"options.json")
repeticoes = options.get('repeticoes_por_config', 1)

print(f"\n\nIniciando configuração {config_num} com os params.json:\n{params}\n")


# Instancia do Setup com a função objetivo
setup = Setup(
    params,
    fitness_function=funcao_objetivo_IEEE14,
    tamanho_hash=get_hash_table_size()
)
print("Classe Setup iniciada para a configuração.")


consultaHashTable()


# Loop de repetições com uma configuração Única
for exec_num in range(1, repeticoes + 1):
    print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")

    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print("Algoritmo Evolutivo iniciado.")

    pop_with_repopulation, logbook_with_repopulation, best_individual, _ = alg.run(RCE=True)

    print("\nEvolução concluída  - 100%")

    best_solution_generation, best_solution_variables, best_solution_fitness, grafico_RCE = alg.dashboard.visualize(
        logbook_with_repopulation,
        pop_with_repopulation,
        config_num=config_num,
        execution_num=exec_num,
    )
    
    print(f"Objective functions runs: {setup.objectiveruns}")
    print(f"Consultas HashTable: {setup.hashtablereads}\n")
    
    print(f"\nMelhores horários de agendamento (melhor indivíduo):")
    print(best_solution_variables)
    print(f"Na melhor geração encontrada = {best_solution_generation} de {setup.params['NUM_GENERATIONS']} ")
    print("="*80)
```

## Análise do Código em POO

1.  **Imports e Separação de Responsabilidades**:
    -   `from AlgEvolutivoRCE_backup...`: Importa as classes do **núcleo do framework**. `Setup` é a classe de configuração e `AlgoritimoEvolutivoRCE` é a classe principal do motor genético.
    -   `from utils.functions_fitness...`: Importa a **definição do problema específico**. `funcao_objetivo_IEEE14` é a função que o algoritmo tentará otimizar. Isso mostra uma excelente separação: o framework é agnóstico ao problema, e o problema é injetado nele.

2.  **Carregamento de Configurações**:
    -   `load_params(...)`: Antes de instanciar qualquer objeto, o script carrega os parâmetros de arquivos externos (`.json`). Isso é uma boa prática que evita "hardcoding" (valores fixos no código) e permite que os mesmos objetos sejam usados em diferentes experimentos apenas trocando os arquivos de configuração.

3.  **Instanciação do Objeto `Setup`**:
    -   `setup = Setup(...)`: Aqui, um **objeto de configuração** é criado. Este objeto (`setup`) agrega todos os parâmetros e a função de fitness (`funcao_objetivo_IEEE14`) necessários para a execução. Ele funciona como um contêiner de dados estruturado que será passado para o algoritmo, simplificando a comunicação entre as partes do sistema.

4.  **Loop de Execução e Instanciação do Algoritmo**:
    -   `for exec_num in ...`: O loop permite que o mesmo experimento configurado seja executado várias vezes para garantir a robustez estatística dos resultados.
    -   `alg = AlgoritimoEvolutivoRCE(setup, ...)`: Dentro do loop, uma nova **instância do algoritmo** é criada. O objeto `setup` é injetado no construtor do `AlgoritimoEvolutivoRCE`, um exemplo claro de **Injeção de Dependência**. O objeto `alg` agora contém toda a lógica e os dados necessários para rodar uma simulação completa.

5.  **Execução e Coleta de Resultados**:
    -   `pop_final, logbook, ... = alg.run(RCE=True)`: Este é o comando que **dispara o comportamento principal** do objeto `alg`. O método `run()` encapsula toda a complexidade do processo evolutivo. Ao final, ele retorna os resultados: a população final, o logbook de estatísticas e o melhor indivíduo encontrado.

6.  **Visualização e Separação de Interesses**:
    -   `alg.dashboard.visualize(...)`: Após a execução, os resultados são passados para outro objeto, o `dashboard`, que pertence ao `alg`. Este objeto é especializado em **visualização de dados**. Isso demonstra uma forte **separação de interesses**: o objeto `alg` foca na computação e otimização, enquanto o objeto `dashboard` foca na apresentação dos resultados. Um não interfere no outro.
