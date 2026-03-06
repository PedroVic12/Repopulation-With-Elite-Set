<a id="topo"></a>

# Guia Mensal PVRV — Checklists Fixos

## Índice

- [Checklist de Metas: Trilha Fullstack & Desktop (Python, JS, Rust)][sec_checklist-de-metas-trilha-fullstack-desktop-python-js-rust]
- [Modelagem de DB com Python e Sqlite3 com pyspark][sec_modelagem-de-db-com-python-e-sqlite3-com-pyspark]
- [Manutenção de Banco de dados do SIGER x BDT (cadastro de equipamentos elétricos e parametros para PMO)][sec_manutencao-siger-bdt]

<a id="checklist-de-metas-trilha-fullstack-desktop-python-js-rust"></a>
---

# Checklist de Metas: Trilha Fullstack & Desktop (Python, JS, Rust)

---

Este checklist visa integrar as tecnologias mencionadas (Flask, Pandas, PySide6, NextJS, Tauri, Rust) em projetos práticos de complexidade crescente.

## Fase 1: Backend & Processamento de Dados (Python)

Foco: Flask, Pandas, Modelagem de Dados, API REST.

- [ ] **Projeto 1: API de Análise de Dados (Simples)**
  - *Stack:* Flask, Pandas.
  - *Objetivo:* Criar uma rota POST que recebe um arquivo CSV/JSON, processa estatísticas básicas (média, mediana, desvio padrão) com Pandas e retorna um JSON com os resultados.
- [ ] **Projeto 2: Sistema de Gestão de Inventário (CRUD REST)**
  - *Stack:* Flask, SQLAlchemy (ou outro ORM), SQLite/Postgres.
  - *Objetivo:* Criar uma API REST completa com autenticação básica. Rotas para criar, ler, atualizar e deletar produtos.
  - *Meta:* Implementar validação de dados (Pydantic ou Marshmallow).

## Fase 2: Desktop Nativo & GUI (Python)

Foco: PySide6 (Qt for Python).

- [ ] **Projeto 3: Dashboard de Monitoramento de Sistema**
  - *Stack:* PySide6, psutil.
  - *Objetivo:* Criar uma janela desktop que mostra uso de CPU, RAM e Disco em tempo real usando gráficos (PyQtGraph ou Matplotlib integrado).
- [ ] **Projeto 4: Cliente Desktop para Inventário**
  - *Stack:* PySide6, requests.
  - *Objetivo:* Criar uma interface gráfica que consome a API do *Projeto 2*. O usuário deve poder adicionar e ver produtos através do app desktop.

## Fase 3: Frontend Web Moderno (JavaScript/TypeScript)

Foco: NextJS, React, TailwindCSS.

- [ ] **Projeto 5: Landing Page de Portfólio**
  - *Stack:* NextJS, TailwindCSS.
  - *Objetivo:* Site estático simples para listar seus projetos do GitHub (pode consumir a API do GitHub).
- [ ] **Projeto 6: Dashboard Web Analytics**
  - *Stack:* NextJS, Chart.js (ou Recharts).
  - *Objetivo:* Consumir a API do *Projeto 1* ou *Projeto 2* e exibir os dados em gráficos interativos no navegador.

## Fase 4: O Próximo Nível - Performance & Apps Híbridos (Rust & Tauri)

Foco: Rust básico, Tauri (Unindo o Frontend Web com Backend Nativo).

- [ ] **Projeto 7: "Hello World" em Rust CLI**
  - *Stack:* Rust (Cargo).
  - *Objetivo:* Criar uma ferramenta CLI simples em Rust que lê um arquivo de texto e conta as palavras (reimplementação simples do `wc`).
- [ ] **Projeto 8: App de Notas Seguro (Tauri)**
  - *Stack:* Tauri, Rust (Backend), React/NextJS (Frontend).
  - *Objetivo:* Um aplicativo desktop onde o frontend (JS) envia notas para o backend (Rust) salvar arquivos criptografados no disco.
  - *Meta:* Aprender a comunicação IPC (Frontend <-> Backend) no Tauri.

## Fase 5: O Projeto Integrador (Master)

- [ ] **Projeto Final: A Suíte de Produtividade**
  - *Backend Central:* API Flask com Pandas para relatórios pesados.
  - *App Desktop Leve:* Tauri App (Rust+React) para uso diário e widgets.
  - *App Admin:* PySide6 para configurações avançadas do sistema local.

[↑ Topo][topo] — [Próximo ⟶][sec_modelagem-de-db-com-python-e-sqlite3-com-pyspark]

<a id="modelagem-de-db-com-python-e-sqlite3-com-pyspark"></a>
---

# Modelagem de DB com Python e Sqlite3 com pyspark

---

Verificar pasta: /home/pedrov12/Documentos/GitHub/Pikachu-Flask-Server/batcaverna/batcaverna-project/scripts

- [ ] Historico de projetos Github
- [ ] Planilhas Tarefas ONS
- [ ] Planilha Corrige SECO - Mensal
- [ ] Deck Builder - PandaPower/AnaREDE com CLI e arquivos .PWF e uso de banco de dados
- [ ] Case Manager Organon
- [ ] 3 bus, 12 bus e IEEE 30 como caso de estudos com decks

[⟵ Anterior][sec_checklist-de-metas-trilha-fullstack-desktop-python-js-rust] — [↑ Topo][topo] — [Próximo ⟶][sec_manutencao-siger-bdt]

<a id="manutencao-siger-bdt"></a>
---

# Manutenção de Banco de dados do SIGER x BDT (cadastro de equipamentos elétricos e parametros para PMO)

---

- [ ] Todo dia 10, o programa roda no SIGER que aponta os equipamentos que estão fora da "ponte" (da Planilha Acompanhamento_PONTE_PL.xlsx: Nas Abas: LTs_SIGER_ForaPonte e TRs_SIGER_ForaPonte)
- [x] GERCAD -> JOB -> ID: Data atual -> Job Criado
- [x] Lts: Coluna T: Deve estar na ponte? Usar apenas as linhas que **NÃO** estão na cor vermelho.
- [x] Separar o Norte, Nordeste, Centroeste e Sudeste para as tarefas. Não cadastrar os que são Data Centers
- [x] Busca por LTS dentro do sistema: GERCARD -> Topologia -> "Estado" -> "Nome Curto da Instação" -> Aplicar critério -> Retorna tudo relacionado a Subestação pesquisada.
- [x] Verificar se ja existe a estação no BDT, botão direito -> Novo Equipamento -> LTR
- [x] **Campos obrigatórios de cadastro:** Numero do circuito do planejamento, Nome Estação, Num Barra preferencial, Tipo Rede: (BASICA), Utilização: PAR,

- [x] Ao final do dia, sempre finalizar o Job feito.

[⟵ Anterior][sec_modelagem-de-db-com-python-e-sqlite3-com-pyspark] — [↑ Topo][topo]

---

[topo]: #topo
[sec_checklist-de-metas-trilha-fullstack-desktop-python-js-rust]: #checklist-de-metas-trilha-fullstack-desktop-python-js-rust
[sec_modelagem-de-db-com-python-e-sqlite3-com-pyspark]: #modelagem-de-db-com-python-e-sqlite3-com-pyspark
[sec_manutencao-siger-bdt]: #manutencao-siger-bdt
