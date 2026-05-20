import streamlit as st
import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from io import StringIO
import numpy as np

class AutomateAnaREDE:
    def __init__(self):
        self.fluxos = []
        self.base_case = "CASO_16_BARRAS.SAV"
        
    def add_fluxo(self, tipo, comentario, comandos):
        """Adiciona um novo fluxo de potência à sequência"""
        self.fluxos.append({
            "tipo": tipo,
            "comentario": comentario,
            "comandos": comandos
        })
    
    def remove_fluxo(self, index):
        """Remove um fluxo da sequência"""
        if 0 <= index < len(self.fluxos):
            del self.fluxos[index]
    
    def get_fluxos(self):
        """Retorna todos os fluxos configurados"""
        return self.fluxos
    
    def set_base_case(self, filename):
        """Define o arquivo de caso base"""
        self.base_case = filename
        
    def generate_dat_content(self):
        """Gera o conteúdo do arquivo .dat"""
        content = StringIO()
        
        # Cabeçalho
        content.write("(==========================================\n")
        content.write("(sistema 16 barras - birds - todas as tensões controladas\n")
        content.write("(==========================================\n")
        content.write(f"(Carrega o caso base em .SAV e ULOG (CASO 2)\n")
        content.write("ULOG\n")
        content.write("2\n")
        content.write(f"{self.base_case}\n")
        content.write("ARQV REST \n")
        content.write("2\n")
        
        # Adiciona todos os fluxos configurados
        for idx, fluxo in enumerate(self.fluxos, 1):
            content.write(f"({fluxo['comentario']}\n")
            content.write(f"{fluxo['tipo']}\n")
            for cmd in fluxo['comandos']:
                content.write(f"{cmd}\n")
            content.write(f"(Fluxo de Potencia - {idx}\n")
            content.write("EXLF\n")
        
        content.write("FIM\n")
        return content.getvalue()

class SimulateApp:
    def __init__(self):
        self.net = self.create_network()
        self.resultados = []
        self.automate = AutomateAnaREDE()
        st.set_page_config(layout="wide")
        st.title("Controle de Fluxo de Potência - 16 Barras")
    
    def create_network(self):
        net = pp.create_empty_network()

        # Criar barras principais
        bus10 = pp.create_bus(net, vn_kv=230, name="CANARIO-10", type='slack')
        bus11 = pp.create_bus(net, vn_kv=230, name="SABIA-11", type='pv')
        bus20 = pp.create_bus(net, vn_kv=230, name="GAVIAO-20", type='pv')
        bus21 = pp.create_bus(net, vn_kv=230, name="URUTAU-21", type='pv')

        # Criar outras 12 barras
        bus_names = ["BARRA-12", "BARRA-13", "BARRA-14", "BARRA-15", 
                    "BARRA-16", "BARRA-17", "BARRA-18", "BARRA-19",
                    "BARRA-22", "BARRA-23", "BARRA-24", "BARRA-25"]

        bus_indices = {}
        bus_indices[10] = bus10
        bus_indices[11] = bus11
        bus_indices[20] = bus20
        bus_indices[21] = bus21
        for i, name in enumerate(bus_names, 12):
            bus_idx = pp.create_bus(net, vn_kv=230, name=name, type='pq')
            bus_indices[i] = bus_idx

        # Adicionar cargas
        for i in range(12, 26):
            if i not in [10, 11, 20, 21]:
                pp.create_load(net, bus_indices[i], p_mw=30, q_mvar=10, name=f'CARGA-{i}')

        # Adicionar geradores
        pp.create_gen(net, bus_indices[10], p_mw=0, vm_pu=1.0, name='GER-SWING')
        pp.create_gen(net, bus_indices[11], p_mw=100, vm_pu=1.05, name='GER-SABIA')
        pp.create_gen(net, bus_indices[20], p_mw=50, vm_pu=1.0, name='GER-GAVIAO')
        pp.create_gen(net, bus_indices[21], p_mw=50, vm_pu=1.0, name='GER-URUTAU')

        # Adicionar linhas (topologia simplificada)
        # Conecta os barramentos em sequência
        for i in range(10, 25):
            if (i+1) in bus_indices:
                pp.create_line(net, from_bus=bus_indices[i], to_bus=bus_indices[i+1], length_km=50, 
                            std_type="NAYY 4x50 SE", name=f"LINHA-{i}-{i+1}")

        # Adicionar trafo
        pp.create_transformer(net, hv_bus=bus_indices[10], lv_bus=bus_indices[11], std_type="0.4 MVA 20/0.4 kV", name="TRAFO-10-11")

        # Definir coordenadas para plotagem
        self.set_geodata(net)

        return net
    
    def set_geodata(self, net):
        # Criar layout em forma de árvore com slack no centro
        net.bus_geodata = pd.DataFrame(index=net.bus.index, columns=['x', 'y'])
        
        # Slack no centro
        net.bus_geodata.loc[0, ['x', 'y']] = (0, 0)
        
        # Demais barras em círculo
        n_buses = len(net.bus)
        radius = 5
        for i in range(1, n_buses):
            angle = 2 * np.pi * i / (n_buses - 1)
            net.bus_geodata.loc[i, 'x'] = radius * np.cos(angle)
            net.bus_geodata.loc[i, 'y'] = radius * np.sin(angle)
    
    def plot_network(self, net, result_idx=-1):
        if not hasattr(net, 'res_bus') or net.res_bus.empty:
            pp.runpp(net)
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Plotar elementos
        plot.simple_plot(net, ax=ax)
        
        # Adicionar tensões como anotações
        bus_geodata = net.bus_geodata
        for idx, row in net.res_bus.iterrows():
            x, y = bus_geodata.loc[idx, 'x'], bus_geodata.loc[idx, 'y']
            voltage = row['vm_pu']
            color = 'green' if 0.95 <= voltage <= 1.05 else 'red'
            ax.text(x, y + 0.2, f"{voltage:.4f} pu", 
                   color=color, fontsize=9, ha='center', 
                   bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        
        # Adicionar título
        title = "Diagrama Unifilar da Rede"
        if result_idx >= 0:
            title += f" (Fluxo {result_idx+1})"
        ax.set_title(title, fontsize=14)
        
        plt.tight_layout()
        return fig
    
    def run_simulation(self, q_lims, v_fluxo2, v_fluxo3, v_fluxo4):
        resultados = []
        
        # Fluxo 1: Modificar limites de reativo
        for bus, q_lim in q_lims.items():
            self.net.gen.loc[self.net.gen.bus==bus, 'max_q_mvar'] = q_lim
        pp.runpp(self.net)
        resultados.append(self.net.res_bus.copy())
        
        # Fluxo 2: Reset de tensões
        for bus, vm in v_fluxo2.items():
            # Note: Alterando a tensão de referência dos geradores (barras PV)
            gen_idx = self.net.gen[self.net.gen.bus == bus].index
            if not gen_idx.empty:
                self.net.gen.loc[gen_idx, 'vm_pu'] = vm
        pp.runpp(self.net)
        resultados.append(self.net.res_bus.copy())
        
        # Fluxo 3: Tensões específicas na barra swing e gerador
        for bus, vm in v_fluxo3.items():
            gen_idx = self.net.gen[self.net.gen.bus == bus].index
            if not gen_idx.empty:
                self.net.gen.loc[gen_idx, 'vm_pu'] = vm
        pp.runpp(self.net)
        resultados.append(self.net.res_bus.copy())
        
        # Fluxo 4: Ajustes finais
        for bus, vm in v_fluxo4.items():
            gen_idx = self.net.gen[self.net.gen.bus == bus].index
            if not gen_idx.empty:
                self.net.gen.loc[gen_idx, 'vm_pu'] = vm
        pp.runpp(self.net)
        resultados.append(self.net.res_bus.copy())
        
        return resultados
    
    def configure_automation(self, q_lims, v_fluxo2, v_fluxo3, v_fluxo4):
        """Configura os fluxos no AutomateAnaREDE"""
        self.automate = AutomateAnaREDE()
        
        # Função para converter tensão para formato de 4 dígitos
        def format_voltage(v):
            return f"{int(v * 1000):04d}"
        
        # Fluxo 1: Limites de reativo
        self.automate.add_fluxo(
            "DBAR IMPR",
            "Modificações nas 4 barras tipo 1 (PV) com controle Potencia ativa/reativa",
            [
                "(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)",
                f"11   M                           {int(q_lims[11])}",
                f"20   M                           {int(q_lims[20])}",
                f"21   M                           {int(q_lims[21])}",
                "99999"
            ]
        )
        
        # Fluxo 2: Reset de tensões
        self.automate.add_fluxo(
            "DBAR IMPR",
            "RESETA todas as 4 barras tipo 1 (PV) com controle de Tensão nos limites estabelecidos: 0,95 pu e 1,05pu",
            [
                "(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)",
                f"10   M                  {format_voltage(v_fluxo2[10])}",
                f"11   M                  {format_voltage(v_fluxo2[11])}",
                f"20   M                  {format_voltage(v_fluxo2[20])}",
                f"21   M                  {format_voltage(v_fluxo2[21])}",
                "99999"
            ]
        )
        
        # Fluxo 3: Aumento lado esquerdo
        self.automate.add_fluxo(
            "DBAR IMPR",
            "Controle de Tensão: AUMENTO DO LADO ESQUERDO na barra SWING - CANARIO-10 e Na barra principal com Gerador - SABIA-11",
            [
                "(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)",
                f"10   M                  {format_voltage(v_fluxo3[10])}",
                f"11   M                  {format_voltage(v_fluxo3[11])}",
                "99999"
            ]
        )
        
        # Fluxo 4: Diminuição lado direito
        self.automate.add_fluxo(
            "DBAR IMPR",
            "Controle Tensão: DIMINUIÇÃO DO LADO DIREITO na barra GAVIAO-20 e URUTAU-21",
            [
                "(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)",
                f"20   M                  {format_voltage(v_fluxo4[20])}",
                f"21   M                  {format_voltage(v_fluxo4[21])}",
                "99999"
            ]
        )
    
    def run(self):
        # Configurações na barra lateral
        st.sidebar.header("Configurações dos Fluxos")
        
        # Fluxo 1: Limites de reativo
        st.sidebar.subheader("Fluxo 1: Controle P/Q")
        q_lims = {
            11: st.sidebar.number_input("Barra 11 - Limite Q (Mvar)", value=300.0),
            20: st.sidebar.number_input("Barra 20 - Limite Q (Mvar)", value=300.0),
            21: st.sidebar.number_input("Barra 21 - Limite Q (Mvar)", value=300.0)
        }
        
        # Fluxo 2: Reset de tensões
        st.sidebar.subheader("Fluxo 2: Reset de Tensões")
        v_fluxo2 = {
            10: st.sidebar.slider("Barra 10 (V_pu)", 0.90, 1.10, 1.05, key='v2_10'),
            11: st.sidebar.slider("Barra 11 (V_pu)", 0.90, 1.10, 1.05, key='v2_11'),
            20: st.sidebar.slider("Barra 20 (V_pu)", 0.90, 1.10, 0.95, key='v2_20'),
            21: st.sidebar.slider("Barra 21 (V_pu)", 0.90, 1.10, 0.95, key='v2_21')
        }
        
        # Fluxo 3: Aumento lado esquerdo
        st.sidebar.subheader("Fluxo 3: Aumento Lado Esquerdo")
        v_fluxo3 = {
            10: st.sidebar.slider("Barra Swing (V_pu)", 0.95, 1.05, 1.03, key='v3_10'),
            11: st.sidebar.slider("Barra Gerador (V_pu)", 0.95, 1.05, 1.03, key='v3_11')
        }
        
        # Fluxo 4: Diminuição lado direito
        st.sidebar.subheader("Fluxo 4: Diminuição Lado Direito")
        v_fluxo4 = {
            20: st.sidebar.slider("Barra 20 Final (V_pu)", 0.95, 1.05, 0.95, key='v4_20'),
            21: st.sidebar.slider("Barra 21 Final (V_pu)", 0.95, 1.05, 0.95, key='v4_21')
        }
        
        # Botões principais
        col1, col2 = st.columns([1, 1])
        run_success = False
        
        with col1:
            if st.button("Executar Fluxos de Potência", use_container_width=True):
                self.resultados = self.run_simulation(q_lims, v_fluxo2, v_fluxo3, v_fluxo4)
                self.configure_automation(q_lims, v_fluxo2, v_fluxo3, v_fluxo4)
                run_success = True
                st.success("Fluxos executados com sucesso!")
        
        # Exibir rede
        st.subheader("Visualização da Rede")
        fig = self.plot_network(self.net)
        st.pyplot(fig)
        
        # Exibir resultados
        if run_success and self.resultados:
            st.subheader("Resultados dos Fluxos de Potência")
            tab1, tab2, tab3, tab4 = st.tabs(["Fluxo 1", "Fluxo 2", "Fluxo 3", "Fluxo 4"])
            
            with tab1:
                st.dataframe(self.resultados[0].style.format("{:.4f}"), height=500)
                fig1 = self.plot_network(self.net, 0)
                st.pyplot(fig1)
            
            with tab2:
                st.dataframe(self.resultados[1].style.format("{:.4f}"), height=500)
                fig2 = self.plot_network(self.net, 1)
                st.pyplot(fig2)
            
            with tab3:
                st.dataframe(self.resultados[2].style.format("{:.4f}"), height=500)
                fig3 = self.plot_network(self.net, 2)
                st.pyplot(fig3)
            
            with tab4:
                st.dataframe(self.resultados[3].style.format("{:.4f}"), height=500)
                fig4 = self.plot_network(self.net, 3)
                st.pyplot(fig4)
        
        # Botão para salvar o arquivo (só aparece após execução)
        if run_success:
            dat_content = self.automate.generate_dat_content()
            
            with col2:
                st.download_button(
                    label="Salvar case_base.dat",
                    data=dat_content,
                    file_name="case_base.dat",
                    mime="text/plain",
                    use_container_width=True
                )
            
            # Prévia do arquivo
            st.subheader("Prévia do Script .dat")
            st.code(dat_content, language="plaintext")

# Executar a aplicação
if __name__ == "__main__":
    app = SimulateApp()
    app.run()