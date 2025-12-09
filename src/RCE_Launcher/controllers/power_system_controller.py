# src/RCE_Launcher/controllers/power_system_controller.py

from PySide6.QtCore import QObject, Slot
import pandas as pd

from ..models.power_system_model import PowerSystemModel, ResultsRepository

# Imports para gráficos, necessários para criar as figuras
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class PowerSystemController(QObject):
    """
    Controller - Gerencia a interação entre o Model e a View da Análise de SEP.
    """
    def __init__(self, view, network_name, agendamento_df, contingencia_df):
        super().__init__()
        self.view = view
        self.model = PowerSystemModel(network_name)
        
        # Dados específicos do caso carregado
        self.agendamento_df = agendamento_df
        self.contingencia_df = contingencia_df
        
        self.current_contingencies = []
        
        self._setup_connections()
        self._initial_load()

    def _setup_connections(self):
        """Conecta os sinais da View aos slots deste controller."""
        self.view.run_simulation_requested.connect(self.run_simulation)
        self.view.contingencies_changed.connect(self.prepare_contingencies)

    def _initial_load(self):
        """Carrega os dados iniciais na View."""
        self.view.update_status("Pronto para simular.")
        self._update_contingency_list()
        self.view.network_canvas.plot_network(self.model.net)
        self.clear_results()

    def _update_contingency_list(self):
        """Popula a lista de contingências na sidebar da View."""
        self.view.contingency_list.clear()
        if self.contingencia_df is not None and not self.contingencia_df.empty:
            for idx, row in self.contingencia_df.iterrows():
                # Assumindo que os IDs das linhas no pandapower correspondem aos do DataFrame
                # Esta é uma simplificação e pode precisar de um mapeamento mais robusto
                # para redes complexas.
                line_id = int(row.get('line_id', idx)) 
                from_bus = row.get('from', 'N/A')
                to_bus = row.get('to', 'N/A')
                
                item = self.view.contingency_list.item_class(f"[L] Ramo {from_bus} ↔ {to_bus}")
                item.setData(Qt.UserRole, ('line', line_id))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.view.contingency_list.addItem(item)

    @Slot(list)
    def prepare_contingencies(self, contingencies: list):
        """Prepara a rede para uma nova simulação com base nas contingências selecionadas."""
        self.current_contingencies = contingencies
        self.model.apply_contingencies(self.current_contingencies)
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net) # Atualiza o diagrama

    @Slot()
    def run_simulation(self):
        """Executa o fluxo de potência e atualiza a View com os resultados."""
        try:
            self.model.apply_contingencies(self.current_contingencies) # Garante que está no estado certo
            success, msg = self.model.run_power_flow()
            self.view.update_status(msg, not success)
            if success:
                self.update_results_display()
            else:
                self.clear_results()
        except Exception as e:
            self.view.update_status(f"Erro crítico na simulação: {e}", True)
            print(traceback.format_exc())
    
    def update_results_display(self):
        """Atualiza os gráficos e tabelas com os novos resultados."""
        try:
            repo = ResultsRepository(self.model.net)
            
            # Atualiza tabelas
            voltage_df = repo.get_bus_voltage_data()
            line_df = repo.get_line_loading_data()
            self.view.update_table(self.view.voltage_table, voltage_df)
            self.view.update_table(self.view.line_loading_table, line_df)
            
            # Atualiza gráficos Plotly se disponível
            if PLOTLY_AVAILABLE:
                fig_v = go.Figure(data=[go.Bar(x=voltage_df['Barra'], y=voltage_df['Tensão (p.u.)'], name='Tensão')])
                fig_v.add_hline(y=1.05, line_dash="dash", line_color="red")
                fig_v.add_hline(y=0.95, line_dash="dash", line_color="red")
                fig_v.update_layout(title_text='Tensão nas Barras (p.u.)')
                self.view.voltage_plot.plot_chart(fig_v)
                
                fig_l = go.Figure(data=[go.Bar(x=line_df['Linha'], y=line_df['Carreg. (%)'], name='Carregamento')])
                fig_l.add_hline(y=100, line_dash="dash", line_color="red")
                fig_l.update_layout(title_text='Carregamento das Linhas (%)')
                self.view.line_loading_plot.plot_chart(fig_l)

        except Exception as e:
            self.view.update_status(f"Erro ao exibir resultados: {e}", True)
            print(traceback.format_exc())

    def clear_results(self):
        """Limpa todos os resultados da View."""
        self.view.update_table(self.view.voltage_table, pd.DataFrame())
        self.view.update_table(self.view.line_loading_table, pd.DataFrame())
        self.view.voltage_plot.clear()
        self.view.line_loading_plot.clear()
