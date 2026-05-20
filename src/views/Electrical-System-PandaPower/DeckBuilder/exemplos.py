from SEP import SEP_Network

# ================== EXEMPLOS ==================


def exemplo_3_barras():
    """Cria uma rede simples de 3 barras (fictícia) usando a classe."""
    dados = {
        "barras": [
            {"nome": "Barra A", "vn_kv": 138.0, "x": 0, "y": 0},
            {"nome": "Barra B", "vn_kv": 138.0, "x": 4, "y": 0},
            {"nome": "Barra C", "vn_kv": 13.8, "x": 2, "y": -2},
        ],
        "linhas": [
            {
                "de": "Barra A",
                "para": "Barra B",
                "comprimento_km": 10,
                "std_type": "NAYY 4x150 SE",
            }
        ],
        "transformadores": [
            {
                "hv": "Barra B",
                "lv": "Barra C",
                "sn_mva": 20,
                "vn_hv_kv": 138.0,
                "vn_lv_kv": 13.8,
                "vkr_percent": 0.5,
                "vk_percent": 8.0,
                "pfe_kw": 30,
                "i0_percent": 0.2,
            }
        ],
        "cargas": [{"barra": "Barra C", "p_mw": 10, "q_mvar": 5}],
        "rede_externa": {"barra": "Barra A", "vm_pu": 1.02},
    }

    rede = SEP_Network(dados)
    rede.criar_rede()
    rede.resolver_fluxo_potencia()
    rede.plotar_diagrama("diagrama_3b.png")
    print("\nExemplo 3 barras concluído.\n")


def exemplo_5_barras():
    """Cria uma rede de 5 barras (baseada em exemplo clássio)."""
    dados = {
        "barras": [
            {"nome": "Barra 1 (ref)", "vn_kv": 230.0, "x": 0, "y": 2},
            {"nome": "Barra 2 (PV)", "vn_kv": 230.0, "x": 3, "y": 3},
            {"nome": "Barra 3 (PQ)", "vn_kv": 230.0, "x": 4, "y": 1},
            {"nome": "Barra 4 (PQ)", "vn_kv": 230.0, "x": 2, "y": 0},
            {"nome": "Barra 5 (PQ)", "vn_kv": 230.0, "x": 5, "y": 2},
        ],
        "linhas": [
            {
                "de": "Barra 1 (ref)",
                "para": "Barra 2 (PV)",
                "comprimento_km": 5,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "Barra 1 (ref)",
                "para": "Barra 4 (PQ)",
                "comprimento_km": 4,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "Barra 2 (PV)",
                "para": "Barra 3 (PQ)",
                "comprimento_km": 3,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "Barra 2 (PV)",
                "para": "Barra 5 (PQ)",
                "comprimento_km": 2,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "Barra 3 (PQ)",
                "para": "Barra 5 (PQ)",
                "comprimento_km": 2.5,
                "std_type": "NAYY 4x150 SE",
            },
        ],
        "cargas": [
            {"barra": "Barra 3 (PQ)", "p_mw": 15, "q_mvar": 5},
            {"barra": "Barra 4 (PQ)", "p_mw": 10, "q_mvar": 3},
            {"barra": "Barra 5 (PQ)", "p_mw": 20, "q_mvar": 8},
        ],
        "rede_externa": {"barra": "Barra 1 (ref)", "vm_pu": 1.0},
    }

    rede = SEP_Network(dados)
    rede.criar_rede()
    rede.resolver_fluxo_potencia()
    rede.plotar_diagrama("diagrama_5b.png")
    print("Exemplo 5 barras concluído.\n")


def exemplo_10_barras():
    """Cria uma rede de 10 barras (inspirada em sistemas de teste)."""
    dados = {
        "barras": [
            {"nome": "B1", "vn_kv": 138.0, "x": 0, "y": 4},
            {"nome": "B2", "vn_kv": 138.0, "x": 2, "y": 5},
            {"nome": "B3", "vn_kv": 138.0, "x": 4, "y": 4},
            {"nome": "B4", "vn_kv": 138.0, "x": 5, "y": 2},
            {"nome": "B5", "vn_kv": 138.0, "x": 3, "y": 1},
            {"nome": "B6", "vn_kv": 13.8, "x": 1, "y": 2},
            {"nome": "B7", "vn_kv": 13.8, "x": 3, "y": 3},
            {"nome": "B8", "vn_kv": 13.8, "x": 5, "y": 4},
            {"nome": "B9", "vn_kv": 13.8, "x": 4, "y": 0},
            {"nome": "B10", "vn_kv": 13.8, "x": 6, "y": 1},
        ],
        "linhas": [
            {
                "de": "B1",
                "para": "B2",
                "comprimento_km": 3,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B2",
                "para": "B3",
                "comprimento_km": 2.5,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B3",
                "para": "B4",
                "comprimento_km": 2,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B4",
                "para": "B5",
                "comprimento_km": 2.2,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B5",
                "para": "B6",
                "comprimento_km": 1.8,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B6",
                "para": "B1",
                "comprimento_km": 2,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B7",
                "para": "B8",
                "comprimento_km": 2,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B8",
                "para": "B9",
                "comprimento_km": 2.3,
                "std_type": "NAYY 4x150 SE",
            },
            {
                "de": "B9",
                "para": "B10",
                "comprimento_km": 1.5,
                "std_type": "NAYY 4x150 SE",
            },
        ],
        "transformadores": [
            {
                "hv": "B3",
                "lv": "B7",
                "sn_mva": 25,
                "vn_hv_kv": 138.0,
                "vn_lv_kv": 13.8,
                "vkr_percent": 0.6,
                "vk_percent": 9.0,
                "pfe_kw": 35,
                "i0_percent": 0.3,
            },
            {
                "hv": "B4",
                "lv": "B8",
                "sn_mva": 20,
                "vn_hv_kv": 138.0,
                "vn_lv_kv": 13.8,
                "vkr_percent": 0.7,
                "vk_percent": 8.5,
                "pfe_kw": 30,
                "i0_percent": 0.25,
            },
            {
                "hv": "B5",
                "lv": "B9",
                "sn_mva": 15,
                "vn_hv_kv": 138.0,
                "vn_lv_kv": 13.8,
                "vkr_percent": 0.8,
                "vk_percent": 8.0,
                "pfe_kw": 25,
                "i0_percent": 0.2,
            },
        ],
        "cargas": [
            {"barra": "B6", "p_mw": 8, "q_mvar": 3},
            {"barra": "B7", "p_mw": 10, "q_mvar": 4},
            {"barra": "B8", "p_mw": 12, "q_mvar": 5},
            {"barra": "B9", "p_mw": 7, "q_mvar": 2},
            {"barra": "B10", "p_mw": 5, "q_mvar": 1.5},
        ],
        "rede_externa": {"barra": "B1", "vm_pu": 1.01},
    }

    rede = SEP_Network(dados)
    rede.criar_rede()
    rede.resolver_fluxo_potencia()
    rede.plotar_diagrama("diagrama_10b.png")
    print("Exemplo 10 barras concluído.\n")


if __name__ == "__main__":
    print("=== Exemplo 3 Barras ===")
    exemplo_3_barras()

    print("=== Exemplo 5 Barras ===")
    exemplo_5_barras()

    print("=== Exemplo 10 Barras ===")
    exemplo_10_barras()

    print("Todos os exemplos executados. Diagramas salvos em PNG.")
