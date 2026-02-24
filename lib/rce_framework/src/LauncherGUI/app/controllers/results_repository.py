class ResultsRepository:
    """Repository - Busca e formata resultados da simulação para a View."""

    def __init__(self, net):
        if net is None or not hasattr(net, "res_bus") or net.res_bus.empty:
            raise ValueError("Rede não simulada ou sem resultados.")
        self.net = net

    def get_kpis(self):
        v_viol = (
            (self.net.res_bus.vm_pu > self.net.bus.max_vm_pu)
            | (self.net.res_bus.vm_pu < self.net.bus.min_vm_pu)
        ).sum()
        l_loads = (
            (self.net.res_line.loading_percent > 100).sum()
            if hasattr(self.net, "res_line")
            else 0
        )
        t_loads = (
            (self.net.res_trafo.loading_percent > 100).sum()
            if hasattr(self.net, "res_trafo")
            else 0
        )
        total_gen = (
            self.net.res_gen.p_mw.sum() if hasattr(self.net, "res_gen") else 0
        ) + (
            self.net.res_ext_grid.p_mw.sum() if hasattr(self.net, "res_ext_grid") else 0
        )
        return {
            "total_load_mw": (
                self.net.res_load.p_mw.sum() if hasattr(self.net, "res_load") else 0
            ),
            "total_gen_mw": total_gen,
            "voltage_violations": int(v_viol),
            "overloads": int(l_loads + t_loads),
        }

    def get_bus_voltage_data(self):
        if hasattr(self.net, "res_bus"):
            return (
                self.net.res_bus[["vm_pu"]]
                .copy()
                .round(4)
                .reset_index()
                .rename(columns={"index": "Barra", "vm_pu": "Tensão (p.u.)"})
            )
        return pd.DataFrame()

    def get_line_loading_data(self):
        if hasattr(self.net, "res_line"):
            return (
                self.net.res_line[["loading_percent"]]
                .copy()
                .round(2)
                .reset_index()
                .rename(columns={"index": "Linha", "loading_percent": "Carreg. (%)"})
            )
        return pd.DataFrame()

