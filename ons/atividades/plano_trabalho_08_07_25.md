# 📅 Plano de Trabalho - 08/07/2025

## ✅ TODO
- [x] Finalizar script de análise de contingência com Pandapower com Streamlit com dashboard online da ONS 
- [ ] Implementar função `read_network()` para ler dados de múltiplas planilhas e diferentes arquivos .SAV, .txt .xlsx .PWF .dat .lst usando pipeline de dados
- [x] Testar fluxo de potência com sistema de 16 barras canarinho controlando o fluxo de potencia invertido. Inferior esquerdo maior tensao e carga
- [ ] Validar resultados com base no caso AnaREDE. Como consegui usar o EditCepel para controlar os scripts do diagrama?

- [x] Pagina de Streamlit analisando cada Case de Rede Eletrica IEEE, inspirado em __http://rbvis02.reger.ons/PIVision/#/Displays/12396/SIN-PI-VISION-CLARO__



## (*) Manual de Uso do AnaREDE e EditCEPEl
- [x] Arquivo caso3.dat tem um script do EditCEPEL para facilitar o uso ao carregar o arquivo .sav. No anaREDE basta clicar no PWF+

- [x] Analise do controle de Tensão e Cargas em Barras do tipo 1 (PV) para 0.95 e 1.05 pu e alterando a Carga de 50 e 500 MW.

- [x] Analisar o sentido de fluxo imaginando o cenário do brasil, nordeste abastece o Sul passando por SP e RJ.

- [x] Analise de geração de energia de telhados fotoVoltaicos das casas em horarios de pico de luz solar e comparando com o que o sistema calculou



## 📊 Análise de Dados
- [ ] Rodar o fluxo de potencia e identificar linhas críticas
- [ ] Gerar gráficos com Plotly (tensões, correntes, potências)
- [ ] Verificar limites de tensão (0.95 a 1.05 pu) e carregamento de linhas (>100%)

## 📝 Documentação
- [ ] Criar o arquivo em .MD com instruções de uso do AnaRede, Simulação com o PandaPower e Testes de agendamentos na rede IEEE 14 com diferentes caso de uso, o memso documento vai servir para o BLOG
- [x] Colocar como output os resultados do Pandapower em Excel (`barras`, `linhas`, `cargas`, `geradores`)
- [ ] Anotar observações sobre diferenças entre AnaREDE e Pandapower e saber estruturar um fluxo de trabalho eficiente para o dia dia da ONS


