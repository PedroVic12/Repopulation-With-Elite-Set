import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot

class PowerSystemModel:
    """Model - Lógica de análise de sistemas de potência com Pandapower."""

    def __init__(self, network_name="case14"):
        self.network_name = network_name
        self.net = self.load_network(network_name)

    def load_network(self, network_name):
        self.network_name = network_name
        try:
            if network_name == "case14":
                self.net = pn.case14()
            elif network_name == "case30":
                self.net = pn.case_ieee30()
            elif network_name == "case118":
                self.net = pn.case118()
            else:
                self.net = pn.case14()
            if self.net and (
                "coords" not in self.net.bus_geodata.columns
                or self.net.bus_geodata.empty
            ):
                plot.create_generic_coordinates(self.net)
            if self.net:
                self.net.name = network_name
            return self.net
        except Exception:
            return pp.create_empty_network()

    def run_power_flow(self):
        if not self.net or self.net.bus.empty:
            return False, "Rede vazia. Impossível executar fluxo de potência."
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, "Fluxo de potência convergiu."
        except pp.LoadflowNotConverged:
            return False, "Fluxo de Potência Não Convergiu."
        except Exception as e:
            return False, f"Erro inesperado: {e}"

    def apply_contingencies(self, contingencies):
        if self.net and not self.net.line.empty:
            self.net.line["in_service"] = True
            for c_type, line_index in contingencies:
                if c_type == "line" and line_index in self.net.line.index:
                    self.net.line.loc[line_index, "in_service"] = False
