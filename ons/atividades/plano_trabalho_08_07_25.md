# 📅 Plano de Trabalho - 08/07/2025

## ✅ TODO
- [ ] Finalizar script de análise de contingência com Pandapower com Streamlit com dashboard online da ONS 
- [ ] Implementar função `read_network()` para ler dados de múltiplas planilhas e diferentes arquivos .json, .txt e .xlsx usando pipeline de dados
- [ ] Testar fluxo de potência com sistema de 16 barras canarinho controlando o fluxo de potencia invertido. Inferior esquerdo maior tensao e carga
- [ ] Validar resultados com base no caso AnaREDE. Como consegui usar o EditCepel para controlar os scripts do diagrama?

## Manual de Uso do AnaREDE e EditCEPEl
- [ ] Arquivo caso3.dat tem um script do EditCEPEL para facilitar o uso ao carregar o arquivo .sav

## 📊 Análise de Dados
- [ ] Rodar o fluxo de potencia e identificar linhas críticas
- [ ] Gerar gráficos com Plotly (tensões, correntes, potências)
- [ ] Verificar limites de tensão (0.95 a 1.05 pu) e carregamento de linhas (>100%)

## 📝 Documentação
- [ ] Criar o arquivo em .MD com instruções de uso do AnaRede, Simulação com o PandaPower e Testes de agendamentos na rede IEEE 14
- [ ] Colocar como output os resultados do Pandapower em Excel (`barras`, `linhas`, `cargas`, `geradores`)
- [ ] Anotar observações sobre diferenças entre AnaREDE e Pandapower

## 🔁 Revisão e Backup
- [ ] Subir projeto para repositório GitHub


