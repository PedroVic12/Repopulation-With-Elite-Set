# frontend.py
import reflex as rx
import requests
import pandas as pd

API_URL = "http://127.0.0.1:5000/ferramentas"

# Classe de design pattern 'State' (Controlador e Modelo do Frontend)
class EstoqueState(rx.State):
    """Gerencia o estado da aplicação frontend."""
    
    # Modelo de dados do frontend
    ferramentas: list[dict] = []
    colunas: list[str] = ["ID", "Nome", "Preço (R$)", "Estoque", "Ações"]
    
    # Estado do formulário para adicionar/editar
    form_data: dict = {"nome": "", "preco": "", "estoque": ""}
    edit_id: int | None = None # Armazena o ID da ferramenta em edição

    # Evento que carrega os dados quando a página é aberta
    @rx.background
    async def load_ferramentas(self):
        async with self:
            try:
                response = requests.get(API_URL)
                response.raise_for_status() # Lança exceção para erros HTTP
                self.ferramentas = response.json()
            except requests.exceptions.RequestException as e:
                print(f"Erro ao carregar ferramentas: {e}")
                # Poderíamos adicionar uma variável de estado para mostrar erro na UI
                self.ferramentas = []

    # Ação para lidar com o envio do formulário (Criar ou Atualizar)
    async def handle_submit(self, form_data: dict):
        """Processa o formulário para criar ou atualizar uma ferramenta."""
        data = {
            "nome": form_data.get("nome"),
            "preco": float(form_data.get("preco", 0)),
            "estoque": int(form_data.get("estoque", 0))
        }
        
        try:
            if self.edit_id is not None:
                # Atualizar (PUT)
                response = requests.put(f"{API_URL}/{self.edit_id}", json=data)
            else:
                # Criar (POST)
                response = requests.post(API_URL, json=data)
            
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erro no submit: {e}")
        
        # Limpa o formulário e recarrega a lista
        self.reset("form_data")
        self.edit_id = None
        return self.load_ferramentas

    # Ação para popular o formulário para edição
    def edit_ferramenta(self, ferramenta: dict):
        self.edit_id = ferramenta["id"]
        # Converte para string para preencher os inputs do formulário
        self.form_data = {
            "nome": ferramenta["nome"],
            "preco": str(ferramenta["preco"]),
            "estoque": str(ferramenta["estoque"]),
        }

    # Ação para deletar uma ferramenta
    async def delete_ferramenta(self, ferramenta_id: int):
        try:
            response = requests.delete(f"{API_URL}/{ferramenta_id}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao deletar: {e}")
        
        return self.load_ferramentas

    # Ação para cancelar a edição
    def cancel_edit(self):
        self.edit_id = None
        self.reset("form_data")


# A Visão (View) da nossa aplicação
def index() -> rx.Component:
    return rx.container(
        rx.heading("Controle de Estoque de Ferramentas Elétricas", size="8", margin_bottom="1em"),
        
        # Formulário para adicionar/editar
        rx.box(
            rx.form(
                rx.vstack(
                    rx.input(placeholder="Nome da Ferramenta", name="nome", value=EstoqueState.form_data["nome"], on_change=EstoqueState.set_form_data, required=True),
                    rx.hstack(
                        rx.input(placeholder="Preço (ex: 299.90)", name="preco", type="number", value=EstoqueState.form_data["preco"], on_change=EstoqueState.set_form_data, required=True),
                        rx.input(placeholder="Estoque", name="estoque", type="number", value=EstoqueState.form_data["estoque"], on_change=EstoqueState.set_form_data, required=True),
                    ),
                    rx.hstack(
                        rx.button("Salvar Ferramenta", type="submit"),
                        rx.button("Cancelar", on_click=EstoqueState.cancel_edit, type="button", color_scheme="gray", variant="soft", is_visible=EstoqueState.edit_id != None),
                        spacing="4"
                    ),
                    spacing="4"
                ),
                on_submit=EstoqueState.handle_submit,
            ),
            padding="2em",
            border="1px solid #ddd",
            border_radius="8px",
            margin_bottom="2em"
        ),
        
        # Tabela de ferramentas
        rx.heading("Estoque Atual", size="6", margin_bottom="1em"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.foreach(EstoqueState.colunas, lambda col: rx.table.column_header_cell(col))
                )
            ),
            rx.table.body(
                rx.foreach(
                    EstoqueState.ferramentas,
                    lambda ferramenta: rx.table.row(
                        rx.table.cell(ferramenta["id"]),
                        rx.table.cell(ferramenta["nome"]),
                        rx.table.cell(f"R$ {ferramenta['preco']:.2f}"),
                        rx.table.cell(ferramenta["estoque"]),
                        rx.table.cell(
                            rx.hstack(
                                rx.button("Editar", on_click=lambda: EstoqueState.edit_ferramenta(ferramenta), size="1"),
                                rx.button("Excluir", on_click=lambda: EstoqueState.delete_ferramenta(ferramenta["id"]), color_scheme="red", variant="soft", size="1"),
                                spacing="2"
                            )
                        ),
                    )
                )
            ),
            variant="surface",
            width="100%"
        ),
        
        # Botão para recarregar os dados manualmente
        rx.button("Atualizar Lista", on_click=EstoqueState.load_ferramentas, margin_top="2em"),
        
        padding_top="2em"
    )

# Configuração e inicialização do app Reflex
app = rx.App()
app.add_page(index, on_load=EstoqueState.load_ferramentas)
app.compile()