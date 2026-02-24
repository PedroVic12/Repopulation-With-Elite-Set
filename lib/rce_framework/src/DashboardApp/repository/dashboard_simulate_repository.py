import pandas as pd


# --- Classe Repositório de Dados ---
class ResultsRepository:
    """
    Classe para buscar e formatar os dados de resultados da rede para os gráficos e KPIs.
    """
    def __init__(self, net):
        if net is None or not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("A rede pandapower não foi simulada ou não contém resultados.")
        self.net = net

    def get_kpis(self):
        """Calcula e retorna os principais indicadores (KPIs) da rede."""
        kpis = {
            "total_load_mw": self.net.res_load.p_mw.sum(),
            "total_gen_mw": self.net.res_gen.p_mw.sum(),
            "voltage_violations": len(self.net.res_bus[self.net.res_bus.vm_pu > self.net.bus.max_vm_pu]) + \
                                  len(self.net.res_bus[self.net.res_bus.vm_pu < self.net.bus.min_vm_pu]),
            "overloads": len(self.net.res_line[self.net.res_line.loading_percent > 100]) + \
                         len(self.net.res_trafo[self.net.res_trafo.loading_percent > 100] if hasattr(self.net, 'res_trafo') else [])
        }
        return kpis

    def get_centralized_generation_data(self):
        """Retorna um DataFrame com os dados de Geração Centralizada (baseado na imagem ONS)."""
        data = {
            'Fonte': ['Hidráulica', 'Eólica', 'Fotovoltaica', 'Térmica', 'Nuclear'],
            'Geração (MW)': [31675, 16416, 6719, 7531, 1365]
        }
        return pd.DataFrame(data)

    def get_distributed_generation_data(self):
        """Retorna um DataFrame com os dados de Geração Distribuída (baseado na imagem ONS)."""
        data = {
            'Fonte': ['MMGD', 'PCH', 'PCT'],
            'Geração (MW)': [10316, 2816, 2054]
        }
        return pd.DataFrame(data)

    def get_bus_voltage_data(self):
        df = self.net.res_bus[['vm_pu']].copy()
        df = df.reset_index().rename(columns={'index': 'Barra', 'vm_pu': 'Tensão (p.u.)'})
        return df

    def get_line_loading_data(self):
        df = self.net.res_line[['loading_percent']].copy()
        df = df.reset_index().rename(columns={'index': 'Linha', 'loading_percent': 'Carregamento (%)'})
        return df

    def get_trafo_loading_data(self):
        if not hasattr(self.net, 'res_trafo') or self.net.res_trafo.empty:
            return pd.DataFrame(columns=['Transformador', 'Carregamento (%)'])
        df = self.net.res_trafo[['loading_percent']].copy()
        df = df.reset_index().rename(columns={'index': 'Transformador', 'loading_percent': 'Carregamento (%)'})
        return df


