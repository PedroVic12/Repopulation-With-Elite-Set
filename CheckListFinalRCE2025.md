# Checklist de Correção de Erros — Projeto Repopulation With Elite Set

## 🧠 Organização
- [ ] Verificar versão do repositório utilizada para análise
- [ ] Criar branch `bugfix/dec-2025` para corrigir erros listados

---

## 1) Configurações geradas mas apenas `config_1` aparece no dashboard
### Sintoma
- Tabelas são preenchidas com *todas* execuções
- Dashboard só visualiza *config_1*

### Causas Possíveis
- Chave primária/id duplicada em tabelas
- Filtro aplicado indevidamente em dashboard
- Loop que sobrescreve config_id

### Ações
- [ ] Verificar geração de IDs no launcher (`config_{i}`)
- [ ] Confirmar que cada execução encerra com `commit` de dados distintos
- [ ] Confirmar que dashboard consulta **tabela completa** sem filtro por config_1
- [ ] Corrigir query/ORM para buscar por config_id dinamicamente

---

## 2) Erro na função objetivo SIN45
