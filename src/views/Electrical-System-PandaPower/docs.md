# Documentação importante do pandapower

- Projetos e tutoriais:
https://www.pandapower.org/start/#interactive-tutorials-

- Salvar e carregar redes:

https://pandapower.readthedocs.io/en/latest/file_io.html

- Diagramas Unifiliar de SEP em pandapower
https://pandapower.readthedocs.io/en/latest/networks/example.html

- Exemplos de uso da lib:

https://github.com/e2nIEE/pandapower/tree/master/tutorials



📚 Resumo dos Documentos do Pandapower
1. Exemplos de Topologia (topology/examples.html)
Conceitos: Demonstra análises topológicas usando networkx em um grafo criado com create_nxgraph.

Funções Chave:

unsupplied_buses: Identifica barras sem conexão com a rede externa.

calc_distance_to_bus: Calcula a distância elétrica (soma dos comprimentos de linha) de uma barra a todas as outras.

connected_components: Encontra componentes conectados, permitindo separar anéis ou partes da rede.

determine_stubs: Identifica ramos "pendentes" (stubs) que partem da rede principal.

Aplicação no seu sistema: Use estas funções para enriquecer a análise pós-fluxo de potência, como destacar ilhas ou caminhos críticos no diagrama.

2. Primeiros Passos (pandapower.org/start/)
Instalação: Recomenda Anaconda e instalação via pip install pandapower[all]. Dependências essenciais: numpy, scipy, pandas, networkx.

Estrutura Básica: Uma rede (net) é um objeto que contém DataFrames do pandas para cada elemento (barras, linhas, trafos, cargas, etc.).

Fluxo de Potência: A função runpp(net) executa o cálculo completo e preenche as tabelas de resultado (ex: net.res_bus, net.res_line).

Tutoriais Interativos: Links para tutoriais em Jupyter sobre análise de dados, fluxo de potência ótimo, curto-circuito, e plotagem com Plotly (essencial para visualização sofisticada).

3. Redes de Exemplo (networks/example.html)
example_simple(): Rede didática com elementos básicos.

example_multivoltage(): Rede realística com múltiplos níveis de tensão (HV, MV, LV), topologias típicas (anel aberto, barramento duplo) e diversos tipos de elementos.

Aplicação: Use estas funções para criar redes de teste rapidamente ou como base para importar dados de outros formatos.

4. Entrada e Saída de Dados (file_io.html)
Formatos Suportados: Pickle, Excel, JSON, SQLite, PostgreSQL.

Aviso Importante: O uso de Excel (to_excel/from_excel) é altamente desencorajado pela própria documentação devido a perdas de conversão. Prefira JSON ou SQLite.

Funções para SQLite:

to_sqlite(net, filename, include_results=False): Salva a rede.

from_sqlite(filename): Carrega a rede.

Importação de Dados: A documentação não menciona diretamente o formato .pwf do AnaREde. No entanto, o submódulo pandapower.converter (mencionado nos requisitos de instalação) pode conter ferramentas para isso. Você precisará investigar funções específicas como pandapower.converter.from_anarede() ou similar, ou criar um conversor personalizado que leia o arquivo texto e populhe a rede com as funções create_*.