#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start - Exemplo Didático de Uso do Pandapower

Este script demonstra como criar e simular uma rede elétrica simples
utilizando a biblioteca pandapower, a base do framework RCE.

Autor: Pedro Victor Veras
Data: 2025
"""

import pandapower as pp
import pandas as pd

def criar_rede_exemplo():
    """Cria uma rede elétrica simples com 4 barras para demonstração."""
    print("🔌 Criando uma rede elétrica de exemplo...")
    net = pp.create_empty_network()

    # Adiciona as barras (nós do sistema)
    b1 = pp.create_bus(net, vn_kv=20., name="Barra de Geração (Slack)")
    b2 = pp.create_bus(net, vn_kv=20., name="Barra de Carga Principal")
    b3 = pp.create_bus(net, vn_kv=20., name="Barra de Carga Secundária")
    b4 = pp.create_bus(net, vn_kv=20., name="Barra com Geração Distribuída")

    # Adiciona a fonte principal de energia (Rede Externa/Slack)
    pp.create_ext_grid(net, bus=b1, vm_pu=1.02, name="Conexão à Rede Principal")

    # Adiciona as linhas de transmissão
    pp.create_line(net, from_bus=b1, to_bus=b2, length_km=10., std_type="NA2XS2Y 1x240/25 12/20 kV", name="Linha 1-2")
    pp.create_line(net, from_bus=b2, to_bus=b3, length_km=5., std_type="NA2XS2Y 1x120/15 12/20 kV", name="Linha 2-3")
    pp.create_line(net, from_bus=b1, to_bus=b3, length_km=8., std_type="NA2XS2Y 1x120/15 12/20 kV", name="Linha 1-3")
    pp.create_line(net, from_bus=b3, to_bus=b4, length_km=4., std_type="NA2XS2Y 1x50/10 12/20 kV", name="Linha 3-4")

    # Adiciona as cargas (consumidores)
    pp.create_load(net, bus=b2, p_mw=0.10, q_mvar=0.05, name="Carga Principal")
    pp.create_load(net, bus=b3, p_mw=0.05, q_mvar=0.02, name="Carga Secundária")

    # Adiciona um gerador distribuído (ex: painel solar)
    pp.create_sgen(net, bus=b4, p_mw=0.03, q_mvar=0.01, name="Geração Solar")
    
    print("✅ Rede de exemplo criada com sucesso!")
    return net

def executar_fluxo_de_potencia(net):
    """Executa o cálculo de fluxo de potência na rede."""
    print("\n⚡ Executando o fluxo de potência...")
    try:
        pp.runpp(net)
        print("✅ Fluxo de potência convergiu!")
        return True
    except pp.LoadflowNotConverged:
        print("❌ ERRO: O fluxo de potência não convergiu. Verifique os dados da rede.")
        return False

def exibir_resultados(net):
    """Exibe os resultados da simulação de forma clara."""
    print("\n📊 Resultados da Simulação:")
    print("="*30)
    
    print("\n--- Tensões nas Barras ---")
    print(net.res_bus)
    
    print("\n--- Carregamento das Linhas ---")
    print(net.res_line)
    
    print("\n--- Potência nas Cargas ---")
    print(net.res_load)

    print("\n--- Potência dos Geradores ---")
    print(net.res_sgen)
    print("="*30)

def main():
    """Função principal que orquestra a demonstração."""
    print("🚀 Início do Quick Start - Pandapower Didático 🚀")
    
    # 1. Criar a rede
    minha_rede = criar_rede_exemplo()
    
    # 2. Executar a simulação
    if executar_fluxo_de_potencia(minha_rede):
        # 3. Exibir os resultados
        exibir_resultados(minha_rede)
        
    print("\n🎉 Demonstração concluída! 🎉")
    print("Este script é a base para entender como o framework RCE simula redes elétricas.")

if __name__ == "__main__":
    main()