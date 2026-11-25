import pandapower as pp

rede = pp.create_empty_network()


barra_swing = pp.create_bus(net,vn_kv=20.0,  name = "Barra 0 SWING")

bus1 = pp.create_bus(net,vn_kv=100,  name = "Barra 1 - Geração PV")

bus2 = pp.create_bus(net,vn_kv=0.4,  name = "Barra 2")
bus3 = pp.create_bus(net,vn_kv=20,  name = "Barra 3")
bus4 = pp.create_bus(net,vn_kv=0.4,  name = "Barra 4")



# Barra de Geração PV
pp.create_ext_grid(net, bus=bu2, vm_pu =1.05, name = "Usina geradora PV")


#Barra de carga 
pp.create_load(net,bus=bus3, p_mw=0.2, q_mvar=0.06, nam"Carga 2")
pp.create_load(net

# Linhas de transmissão
pp.create_line(net, from_bus=b3, to_bus=bus4, lenght_km =0.3, name="Linha", std_type ="


