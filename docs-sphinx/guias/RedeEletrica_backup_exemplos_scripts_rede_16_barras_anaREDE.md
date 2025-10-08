# rede_16_barras_anaREDE.py

```python
def parse_script(content: str) -> list:
    """
    Analisa o script e extrai os cenários de fluxo de potência
    Retorna uma lista de cenários onde cada cenário é uma lista de alterações
    """
    lines = content.split('\n')
    scenarios = []
    current_scenario = []
    in_dbar_block = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("(Fluxo de Potencia -"):
            if current_scenario:
                scenarios.append(current_scenario)
                current_scenario = []
        
        elif line.startswith("DBAR IMPR"):
            in_dbar_block = True
            continue
        
        elif line == "99999":
            in_dbar_block = False
            continue
        
        elif in_dbar_block and line and not line.startswith('('):
            # Processa linhas de dados
            parts = line.split()
            if len(parts) >= 4:
                bar_num = int(parts[0])
                # Identifica o tipo: 0 para gerador, 1 para barra
                # (geradores têm valores na coluna Qg, barras na coluna V)
                if parts[3].isdigit():  # Valor numérico na coluna Qg (gerador)
                    value = float(parts[3])
                    current_scenario.append(('gerador', bar_num, value))
                elif len(parts[2]) == 4 and parts[2].isdigit():  # Coluna V (tensão)
                    voltage = float(parts[2]) / 1000  # Converte 1050 para 1.050
                    current_scenario.append(('barra', bar_num, voltage))
    
    if current_scenario:
        scenarios.append(current_scenario)
    
    return scenarios

def create_scenario_matrix(scenarios: list) -> list:
    """
    Cria a matriz de cenários no formato especificado
    """
    scenario_matrix = []
    
    for scenario in scenarios:
        scenario_row = []
        for item in scenario:
            # Primeiro valor: 0 para gerador, 1 para barra
            item_type = 0 if item[0] == 'gerador' else 1
            scenario_row.extend([item_type, item[1], item[2]])
        
        scenario_matrix.append(scenario_row)
    
    return scenario_matrix

def calculate_load_and_voltage_stats(scenarios: list) -> list:
    """
    Calcula a carga total do sistema e estatísticas de tensão para cada cenário
    """
    stats = []
    
    for scenario in scenarios:
        total_load = 0
        voltages = []
        
        for item in scenario:
            if item[0] == 'gerador':
                # Considera valores positivos como geração
                total_load -= item[2]  # Subtrai a geração da carga total
            elif item[0] == 'barra':
                voltages.append(item[2])
        
        if voltages:
            min_voltage = min(voltages)
            max_voltage = max(voltages)
        else:
            min_voltage = max_voltage = 0
        
        stats.append([total_load, min_voltage, max_voltage])
    
    return stats

# Exemplo de uso
if __name__ == "__main__":
    script_content = """
(==========================================
(sistema 16 barras - birds - todas as tensões controladas
(==========================================
(Carrega o caso base em .SAV e ULOG (CASO 2)
ULOG
2
CASO_16_BARRAS.SAV
ARQV REST 
2
( Modificações nas 4 barras tipo 1 (PV) com controle Potencia ativa/reativa
DBAR IMPR
(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)
11   M                           500
20   M                           150 
21   M                           150
99999
(Fluxo de Potencia - 1
EXLF
( RESETA todas as 4 barras tipo 1 (PV) com controle de Tensão nos limites estabelecidos: 0,95 pu e 1,05pu
DBAR IMPR
(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)
10   M                  1050        
11   M                  1050      
20   M                  0950       
21   M                  0950    
99999
(Fluxo de Potencia - 2
EXLF
( Controle de Tensão: AUMENTO DO LADO ESQUERDO na barra SWING - CANARIO-18 e Na barra principal com Gerador - SABIA-11
DBAR IMPR
(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)
10   M                  0990
11   M                  1020     
99999
(Fluxo de Potencia - 3
EXLF
( Controle Tensão: DIMINUIÇÃO DO LADO DIREITO na barra GAVIAO-13
DBAR IMPR
(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)
20   M                  0970  
21   M                  0950       
99999
(Fluxo de Potencia - 4
EXLF
FIM
"""

    # Processa o script
    scenarios = parse_script(script_content)
    
    # Cria a matriz de cenários
    scenario_matrix = create_scenario_matrix(scenarios)
    
    # Calcula estatísticas de carga e tensão
    load_stats = calculate_load_and_voltage_stats(scenarios)
    
    print("Matriz de Cenários:")
    for i, row in enumerate(scenario_matrix):
        print(f"Cenário {i+1}: {row}")
    
    print("\nEstatísticas de Carga e Tensão:")
    print("| Cenário | Carga Total (MW) | Mín. Tensão (pu) | Máx. Tensão (pu) |")
    for i, (load, vmin, vmax) in enumerate(load_stats):
        print(f"| {i+1:^8} | {load:^16.2f} | {vmin:^16.3f} | {vmax:^16.3f} |")
```