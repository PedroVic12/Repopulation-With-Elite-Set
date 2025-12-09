# src/RCE_Launcher/models/power_system_model.py

import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot

class PowerSystemModel:
    """Model - Lógica de análise de sistemas de potência com Pandapower."""
    def __init__(self, network_name="case14"):
        self.network_name = network_name
        self.net = self.load_network(network_name)

    def load_network(self, network_name):
        """Carrega uma rede padrão da biblioteca pandapower."""
        self.network_name = network_name
        try:
            if network_name == "case14": self.net = pn.case14()
            elif network_name == "case30": self.net = pn.case_ieee30()
            elif network_name == "case118": self.net = pn.case118()
            elif network_name == "New Network": self.net = pp.create_empty_network(name="New Network")
            else: self.net = pn.case14() # Fallback

            # Garante que a rede tenha coordenadas geográficas para plotagem
            if self.net and ('coords' not in self.net.bus_geodata.columns or self.net.bus_geodata.empty):
                 plot.create_generic_coordinates(self.net)

            if self.net:
                self.net.name = network_name
            return self.net
        except Exception:
            return pp.create_empty_network()

    def run_power_flow(self):
        """Executa o cálculo de fluxo de potência."""
        if not self.net or self.net.bus.empty:
            return False, "Rede está vazia. Não é possível executar o fluxo de potência."
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, "Fluxo de potência convergiu com sucesso."
        except pp.LoadflowNotConverged:
            return False, "Fluxo de Potência Não Convergiu."
        except Exception as e:
            return False, f"Ocorreu um erro inesperado no fluxo de potência: {e}"

    def apply_contingencies(self, contingencies):
        """Aplica uma lista de contingências (desligamentos de linha) na rede."""
        if self.net and not self.net.line.empty:
            # Primeiro, reseta todas as linhas para 'em serviço'
            self.net.line['in_service'] = True
            # Depois, aplica as contingências selecionadas
            for c_type, c_id in contingencies:
                # O 'c_id' aqui é o índice da linha no DataFrame de contingência, que deve corresponder ao índice no pandapower
                if c_type == 'line' and c_id in self.net.line.index:
                    self.net.line.loc[c_id, 'in_service'] = False


class ResultsRepository:
    """Repository - Busca e formata resultados da simulação para a View."""
    def __init__(self, net):
        if net is None or not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("A rede não foi simulada ou não contém resultados para o repositório.")
        self.net = net

    def get_kpis(self):
        """Calcula e retorna os principais indicadores de desempenho (KPIs)."""
        voltage_violations = ((self.net.res_bus.vm_pu > self.net.bus.max_vm_pu) | (self.net.res_bus.vm_pu < self.net.bus.min_vm_pu)).sum()
        line_overloads = (self.net.res_line.loading_percent > 100).sum()
        
        trafo_overloads = 0
        if hasattr(self.net, 'res_trafo') and not self.net.res_trafo.empty:
            trafo_overloads = (self.net.res_trafo.loading_percent > 100).sum()

        total_gen = 0
        if hasattr(self.net, 'res_gen') and not self.net.res_gen.empty:
            total_gen += self.net.res_gen.p_mw.sum()
        if hasattr(self.net, 'res_ext_grid') and not self.net.res_ext_grid.empty:
            total_gen += self.net.res_ext_grid.p_mw.sum()


        return {
            "total_load_mw": self.net.res_load.p_mw.sum() if hasattr(self.net, 'res_load') else 0,
            "total_gen_mw": total_gen,
            "voltage_violations": int(voltage_violations),
            "overloads": int(line_overloads + trafo_overloads)
        }

    def get_bus_voltage_data(self):
        """Retorna um DataFrame com os dados de tensão das barras."""
        df = self.net.res_bus[['vm_pu']].copy().round(4)
        return df.reset_index().rename(columns={'index': 'Barra', 'vm_pu': 'Tensão (p.u.)'})

    def get_line_loading_data(self):
        """Retorna um DataFrame com os dados de carregamento das linhas."""
        df = self.net.res_line[['loading_percent']].copy().round(2)
        return df.reset_index().rename(columns={'index': 'Linha', 'loading_percent': 'Carreg. (%)'})
