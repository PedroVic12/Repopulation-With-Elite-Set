# Algoritmo Evolutivo RCE: O Coração do Framework

O arquivo `alg_evolutivo_rce.py` representa o núcleo do framework de otimização. Ele implementa um Algoritmo Genético (AG) robusto, potencializado pela estratégia de **Repopulation-with-Elite-Set (RCE)**. Do ponto de vista da Programação Orientada a Objetos (POO), este módulo é um exemplo claro de encapsulamento e orquestração.

## Classe `AlgoritimoEvolutivoRCE`

Esta classe é a peça central que encapsula toda a lógica, estado e comportamento do algoritmo evolutivo. Ela funciona como o "motor" que impulsiona a evolução de uma população de soluções.

### `__init__(self, setup, DEBUG=True)`

O construtor é o ponto de entrada para a criação de uma instância do algoritmo. Ele demonstra um princípio fundamental de POO: a **Injeção de Dependência**.

-   **`setup` (Injeção de Dependência)**: Em vez de criar suas próprias configurações, o algoritmo recebe um objeto `Setup` já configurado. Isso torna a classe `AlgoritimoEvolutivoRCE` altamente desacoplada e modular. Ela não precisa saber *como* os parâmetros foram criados, apenas que o objeto `setup` fornecerá tudo o que ela precisa (tamanho da população, taxa de mutação, etc.).
-   **`DEBUG`**: Um simples booleano para controlar o estado interno de logging, permitindo uma depuração mais fácil sem poluir a saída em produção.

### Principais Métodos: Orquestrando a Evolução

Os métodos desta classe trabalham juntos para executar o processo evolutivo de forma organizada.

-   **`run(self, RCE=False, num_pop=0)`**: Este é o método principal, o orquestrador da classe. Ele executa o loop evolutivo completo, geração por geração. A partir de um único chamado a `run()`, todo o processo de seleção, cruzamento, mutação e avaliação é disparado em sequência.
    -   **`RCE`**: Um parâmetro booleano que atua como um "interruptor" de estratégia, permitindo que o mesmo método `run` execute o algoritmo com ou sem a lógica de Repopulation-with-Elite-Set, mostrando a flexibilidade do design.

-   **`aplicar_RCE(self, generation, current_population)`**: Este método encapsula a lógica específica da estratégia RCE. Ele modifica o estado da população (`current_population`), substituindo uma porção dela por indivíduos de elite e novos indivíduos aleatórios. Em POO, este é um método de "comportamento" que altera o "estado" do objeto.

-   **`criterios_RCE(self, population)`**: Um método de "política" ou "estratégia". Sua única responsabilidade é avaliar a população e selecionar quais indivíduos são dignos de pertencer ao conjunto de elite. Ele abstrai as regras de seleção da elite do processo principal de RCE.

-   **`elitismoSimples(self, pop)`**: Outro método de política que implementa a estratégia de elitismo, garantindo que o melhor indivíduo de uma geração (o "elite") sobreviva para a próxima. Isso preserva a melhor solução encontrada até o momento.

-   **`registrarDados(self, generation)`**: Este método atua como um "observador" (Observer). A cada geração, ele é chamado para coletar e armazenar estatísticas (fitness mínimo, máximo, médio) no `logbook`. Ele não interfere na lógica principal da evolução, apenas a observa e registra, demonstrando uma clara separação de responsabilidades.

## Como Funciona: O Fluxo em POO

1.  **Inicialização (Construtor)**: Um objeto `AlgoritimoEvolutivoRCE` é criado, recebendo suas dependências (o objeto `Setup`). Uma população inicial de "objetos-indivíduo" é gerada.
2.  **Execução (`run`)**: O método `run` inicia o loop evolutivo. A cada iteração (geração), ele orquestra as seguintes ações:
    1.  **Seleção**: Invoca um método (ex: torneio) que seleciona objetos-indivíduo da população para reprodução.
    2.  **Crossover & Mutação**: Gera novos objetos-indivíduo (descendentes) a partir dos pais selecionados.
    3.  **Avaliação**: Calcula o fitness de cada novo indivíduo, atualizando seu estado interno.
    4.  **RCE (se ativado)**: Chama `aplicar_RCE` em intervalos específicos para injetar diversidade na população.
    5.  **Elitismo**: Utiliza `elitismoSimples` para garantir a sobrevivência do melhor indivíduo.
    6.  **Registro**: Chama `registrarDados` para salvar o progresso da geração.
3.  **Finalização**: Ao término do loop, o método `run` retorna os resultados finais: a população de objetos-indivíduo, o `logbook` de estatísticas e o melhor objeto-indivíduo encontrado.