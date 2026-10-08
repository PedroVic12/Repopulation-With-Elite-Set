# Documentação: `RCE_Framework_Page.py`

Este arquivo define a interface de usuário (UI) para a visualização dos resultados do framework RCE, construída com a biblioteca Streamlit. Embora o Streamlit siga um modelo de execução linear, este código foi estruturado utilizando princípios de **Programação Orientada a Objetos (POO)** para criar um sistema modular, reutilizável e de fácil manutenção.

A página é organizada em **componentes**, **controladores de estado** e uma **classe principal** que orquestra tudo.

## Arquitetura Orientada a Objetos da Página

### 1. Componentes Reutilizáveis

Componentes são blocos de construção da UI. Eles podem ser classes ou funções que têm uma responsabilidade única e bem definida: renderizar uma parte específica da interface. Isso evita a repetição de código e facilita a manutenção.

-   **`StatisticsTableComponent` (Classe como Componente)**: Esta classe encapsula a lógica para exibir uma tabela de estatísticas. O uso de um método estático (`render`) a torna um componente "puro" e sem estado: ela apenas recebe dados e os renderiza, sem armazenar informações internamente.

-   **`card_metric`, `CardsSolutions`, `AgendamentoRedePage` (Funções como Componentes)**: Estas funções atuam como componentes que renderizam partes específicas da tela. 
    -   `card_metric`: Cria um único "cartão" de métrica. É um componente de baixo nível.
    -   `CardsSolutions`: Compõe vários cartões de métrica para exibir a solução completa.
    -   `AgendamentoRedePage`: Renderiza a linha do tempo interativa, um componente complexo que encapsula a lógica de visualização do agendamento.

### 2. Controlador de Estado: `TabPinningController`

Esta classe é um exemplo perfeito de como a POO pode ser usada para gerenciar o estado da interface de forma limpa e centralizada.

-   **Propósito**: Sua única responsabilidade é gerenciar a funcionalidade de "fixar aba". Ela controla qual aba está selecionada e se ela deve permanecer visível mesmo quando o usuário navega para outras seções.
-   **Encapsulamento**: A classe encapsula a lógica de estado no `st.session_state`. Métodos como `render_toggle` e `render_selection_box` fornecem uma interface pública e segura para que o resto da aplicação interaja com essa funcionalidade, sem precisar conhecer os detalhes da implementação (como as chaves usadas no `session_state`).

### 3. A Classe Principal: `FrameworkRCEDashboard`

Esta é a classe orquestradora da página. Ela instancia e gerencia todos os outros componentes e controladores, definindo a estrutura geral do dashboard.

-   **`__init__` (Construtor e Injeção de Dependência)**: O construtor inicializa o dashboard. Ele cria instâncias de classes de serviço, como `DatabaseController` e `TabPinningController`. Isso é uma forma de **injeção de dependência**, onde a classe `FrameworkRCEDashboard` recebe as ferramentas de que precisa para trabalhar.

-   **Métodos de Renderização (`renderHeader`, `MenuLateral`, `renderFooter`)**: Em vez de ter um único bloco de código gigante, a UI é dividida em métodos, cada um responsável por renderizar uma parte da página (cabeçalho, menu lateral, rodapé). Isso torna o código muito mais legível e organizado.

-   **`renderExecutionDetails` (Composição de Componentes)**: Este método demonstra a **composição**. Ele busca os dados de uma execução específica e, em seguida, chama outros componentes (`CardsSolutions`, `AgendamentoRedePage`) para renderizar as diferentes partes da visualização de detalhes. Ele compõe uma visão complexa a partir de peças menores.

-   **`run` (O Orquestrador)**: Este é o método principal que executa a página. Ele define a sequência em que a interface é construída: renderiza o cabeçalho, o menu, a tabela de resultados e, finalmente, as abas com os detalhes de cada execução. Ele atua como o maestro, chamando os outros métodos e componentes na ordem correta para montar a página final.

