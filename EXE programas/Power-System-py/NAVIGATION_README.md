# Power System Dashboard - Navigation Architecture

## 📁 Arquivo Structure

```
Power-System-py/
├── SYSTEM_ELECTRICAL_PANDAPOWER.py  # Main application (MVC + UI)
├── routes.py                        # Navigation Router (NEW)
├── styles.py                        # Application styles
├── test_router.py                   # Unit tests for router
└── README.md                        # This file
```

## 🎯 Arquitetura de Navegação

A navegação foi separada em um arquivo dedicado (`routes.py`) para melhorar a manutenibilidade e testabilidade.

### Router Class

A classe `Router` gerencia:
- **Vista ativa** (Results ou New Network Editor)
- **Transições de visualização** 
- **Tema da aplicação** (Dark/Light)
- **Eventos de rede**
- **Callbacks** para diferentes estados

### ViewType Enum

Define os dois modos principais da aplicação:
```python
class ViewType(Enum):
    RESULTS = "results"           # Visualizando resultados da simulação
    NEW_NETWORK = "new_network"   # Editor de rede
```

## 🔄 Fluxo de Navegação

```
┌─────────────────────────────────────────────────────┐
│            Power System Controller                   │
│  (Gerencia Model + View + Router)                   │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    Router      MainWindow   PowerSystemModel
   (routes.py) (navigation)
```

## 📝 Uso do Router

### Inicializar o Router
```python
from routes import Router

router = Router()
view = MainWindow(router)
```

### Navegar entre vistas
```python
# Ir para editor de rede
router.navigate_to("new_network")

# Voltar para resultados
router.navigate_to("results")
```

### Verificar estado
```python
if router.is_in_editor_mode():
    print("Usuário está no editor de rede")

if router.should_show_contingencies():
    print("Mostrar grupo de contingências")
```

### Registrar callbacks
```python
# Callback quando vista mudar
router.register_view_callback("results", lambda: print("Entrando em resultados"))

# Callback quando tema mudar
router.register_theme_callback("ui", lambda theme: apply_theme(theme))

# Callback quando rede carregar
router.register_network_callback("ui", lambda name, obj: update_ui(name))
```

## 🧪 Testando a Navegação

Todos os testes de lógica de roteamento podem ser executados sem GUI:

```bash
python test_router.py
```

Os testes validam:
- ✓ Inicialização do router
- ✓ Navegação entre vistas
- ✓ Togglear tema
- ✓ Callbacks de vista
- ✓ Callbacks de rede
- ✓ Queries de estado
- ✓ Visibilidade de contingências

## 🚀 Executar a Aplicação

```bash
python SYSTEM_ELECTRICAL_PANDAPOWER.py
```

## 📊 Melhorias com o Router

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Lógica de navegação** | Espalhada na MainWindow | Centralizada em `routes.py` |
| **Testabilidade** | Depende de GUI (QT) | Testável sem GUI |
| **Manutenção** | Difícil de rastrear fluxos | Claro e documentado |
| **Extensibilidade** | Novo código na MainWindow | Novos callbacks no Router |
| **Reutilização** | Acoplada à GUI | Desacoplada, reutilizável |

## 🔗 Integração com Existing Code

A navegação é completamente backward-compatible. O `MainWindow` continua funcionando como antes, mas agora usa o `Router`:

```python
# Na MainWindow.__init__()
def __init__(self, router: Router):
    self.router = router
    ...

# Em show_view()
def show_view(self, name):
    if self.router.navigate_to(name):
        self.view_stack.setCurrentIndex(self.router.get_view_index())
        self.sidebar.contingency_group.setVisible(self.router.should_show_contingencies())
```

## 📚 Próximos Passos

### Potenciais melhorias:
1. **Histórico de navegação**: Implementar back/forward
2. **Persistência de estado**: Salvar última vista usada
3. **Validações de transição**: Confirmar antes de sair do editor
4. **Routes guardadas**: Definir rotas complexas predefinidas
5. **Analytics**: Rastrear padrões de navegação do usuário

## 🐛 Troubleshooting

### Router não muda de vista
```python
# Certifique-se de registrar o callback ou chamar get_view_index()
view_index = router.get_view_index()
self.view_stack.setCurrentIndex(view_index)
```

### Contingências não aparecem/desaparecem
```python
# Verificar visibilidade
if not router.should_show_contingencies():
    sidebar.contingency_group.setVisible(False)
```

---

**Autor**: Sistema de Navegação Refatorado  
**Data**: 2025-12-09  
**Status**: ✅ Funcional e testado
