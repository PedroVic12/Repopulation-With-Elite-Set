o @src/run.py tem que funcionar com o @app.py mas eu quero aridiconar o meu app template em
  @src/app_template_desktop.py (este arquivo é so um exemplo) e eu quero adicionar os meus tabs no menu lareal
  e abrir e fechar abas ou tabs nesse meu projeto usando os mesmos imports!!!!!! e usar todo meu projeto com
  um arquivo novo seprado com o codigo completo nele como main_lancher.py

✦ OK. Entendi. Você quer fundir a funcionalidade do app.py (o executor de simulações) com a estrutura de
  interface moderna do src/app_template_desktop.py (menu lateral, abas que fecham, etc.), e consolidar tudo em
  um único arquivo novo chamado main_launcher.py.

  Compreendi a arquitetura que você deseja. Vou seguir este plano:

1. Criar o `main_launcher.py`: Começarei com a base do seu app.py funcional.
2. Redesenhar a Interface: Vou reestruturar a janela principal para ter o layout do seu template: um menu
   lateral retrátil e uma área de conteúdo com abas dinâmicas.
3. Integrar as Funcionalidades: As telas de "Configuração", "Parâmetros AG" e "Logs" do app.py se tornarão
   abas que você poderá abrir e fechar através do novo menu lateral.
4. Finalizar e Unificar: Manterei a lógica de execução do src/run.py e garantirei que todos os caminhos e
   dependências funcionem corretamente a partir do novo arquivo main_launcher.py.
