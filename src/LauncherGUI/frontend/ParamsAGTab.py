
import json


from PySide6.QtWidgets import (
    QPushButton, QVBoxLayout, QWidget, QHBoxLayout,  QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt


class ParamsAGTab(QWidget):
    """Aba para editar todos os parâmetros em tabela (UI Original mantida)."""
    # Parâmetros gerenciados pela outra aba não são mostrados aqui
    EXCLUDED_PARAMS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.reload()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        buttons_layout = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(self.reload_btn)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)

    def reload(self):
        """Recarrega os parâmetros do `params.json`, excluindo os gerenciados em outra aba."""
        self.table.clearContents()
        
        all_params = self.config_manager.db_controller.get_params()
        params_to_show = {
            k: v for k, v in all_params.items() if k not in self.EXCLUDED_PARAMS
        }
        
        
        print("Parametros editáveis para o AG", params_to_show)
        
        self.table.setRowCount(len(params_to_show))
        for r, (key, value) in enumerate(params_to_show.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, key_item)
            
            # Converte listas e dicionários para uma string JSON para exibição
            if isinstance(value, (list, dict)):
                display_value = json.dumps(value)
            else:
                display_value = str(value)
            self.table.setItem(r, 1, QTableWidgetItem(display_value))

    def save(self):
        """Salva os parâmetros da tabela, preservando os que não são mostrados."""
        # Carrega o estado atual do arquivo para não sobrescrever parâmetros ocultos
        params_to_save = self.config_manager.db_controller.get_params()

        # Atualiza com os valores da tabela
        for r in range(self.table.rowCount()):
            key = self.table.item(r, 0).text()
            value_str = self.table.item(r, 1).text().strip()
            
            # Tenta converter para o tipo de dado correto
            # 1. JSON (listas/dicionários)
            if (value_str.startswith('[') and value_str.endswith(']')) or \
               (value_str.startswith('{') and value_str.endswith('}')):
                try:
                    value = json.loads(value_str)
                except json.JSONDecodeError:
                    value = value_str # Mantém como string se o JSON for inválido
            else:
                # 2. Números (int, depois float)
                try:
                    value = int(value_str)
                except ValueError:
                    try:
                        value = float(value_str)
                    except ValueError:
                        value = value_str # Se tudo falhar, é uma string

            params_to_save[key] = value
        
        # --- Validação: ind_size vs array_var (código do usuário mantido) ---
        ind_size = params_to_save.get("ind_size")
        array_var = params_to_save.get("array_var")

        if isinstance(ind_size, int) and isinstance(array_var, list):
            if len(array_var) != ind_size:
                msg = f"Atenção: O tamanho do 'ARRAY_VAR' ({len(array_var)}) é diferente do 'ind_size' ({ind_size}).\n\n Corrija o tamanho das variáveis de decisão e do tamanho do individuo da sua população."
                QMessageBox.warning(self, "Validação de Parâmetros!", msg)
        # --- Fim da Validação ---

        if self.config_manager.db_controller.save_params(params_to_save):
            QMessageBox.information(self, "Sucesso", "Parâmetros salvos.")
            # Recarrega a tabela para mostrar os valores formatados corretamente
            self.reload() 
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar parâmetros.")
