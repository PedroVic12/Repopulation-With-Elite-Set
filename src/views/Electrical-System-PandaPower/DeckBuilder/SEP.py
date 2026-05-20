import pandapower as pp
import pandas as pd
import schemdraw
import schemdraw.elements as elm
import json
from typing import Optional, Dict, List, Union


class SEP_Network:
    """
    Classe para modelagem e visualização de redes elétricas usando pandapower e schemdraw.
    """

    def __init__(self, dados_json: Optional[Union[str, dict]] = None):
        self.net = pp.create_empty_network()
        self.barras_df = pd.DataFrame(columns=["nome", "vn_kv", "x", "y", "index"])
        self.linhas_df = pd.DataFrame(
            columns=["de", "para", "comprimento_km", "std_type", "index"]
        )
        self.transformadores_df = pd.DataFrame(
            columns=[
                "hv",
                "lv",
                "sn_mva",
                "vn_hv_kv",
                "vn_lv_kv",
                "vkr_percent",
                "vk_percent",
                "pfe_kw",
                "i0_percent",
                "index",
            ]
        )
        self.cargas_df = pd.DataFrame(columns=["barra", "p_mw", "q_mvar", "index"])
        self.rede_externa = {}  # {"barra": nome, "vm_pu": valor}

        if dados_json:
            self.carregar_json(dados_json)

    def carregar_json(self, dados: Union[str, dict]):
        """Carrega dados de um arquivo JSON ou dicionário."""
        if isinstance(dados, str):
            with open(dados, "r") as f:
                dados = json.load(f)

        # Preencher DataFrames
        if "barras" in dados:
            self.barras_df = pd.DataFrame(dados["barras"])
        if "linhas" in dados:
            self.linhas_df = pd.DataFrame(dados["linhas"])
        if "transformadores" in dados:
            self.transformadores_df = pd.DataFrame(dados["transformadores"])
        if "cargas" in dados:
            self.cargas_df = pd.DataFrame(dados["cargas"])
        if "rede_externa" in dados:
            self.rede_externa = dados["rede_externa"]

    def adicionar_barra(self, nome: str, vn_kv: float, x: float = 0.0, y: float = 0.0):
        """Adiciona uma barra manualmente."""
        nova_barra = pd.DataFrame(
            [[nome, vn_kv, x, y, None]], columns=["nome", "vn_kv", "x", "y", "index"]
        )
        self.barras_df = pd.concat([self.barras_df, nova_barra], ignore_index=True)

    def adicionar_linha(self, de: str, para: str, comprimento_km: float, std_type: str):
        """Adiciona uma linha manualmente."""
        nova_linha = pd.DataFrame(
            [[de, para, comprimento_km, std_type, None]],
            columns=["de", "para", "comprimento_km", "std_type", "index"],
        )
        self.linhas_df = pd.concat([self.linhas_df, nova_linha], ignore_index=True)

    def adicionar_transformador(
        self,
        hv: str,
        lv: str,
        sn_mva: float,
        vn_hv_kv: float,
        vn_lv_kv: float,
        vkr_percent: float,
        vk_percent: float,
        pfe_kw: float,
        i0_percent: float,
    ):
        """Adiciona um transformador manualmente."""
        novo_trafo = pd.DataFrame(
            [
                [
                    hv,
                    lv,
                    sn_mva,
                    vn_hv_kv,
                    vn_lv_kv,
                    vkr_percent,
                    vk_percent,
                    pfe_kw,
                    i0_percent,
                    None,
                ]
            ],
            columns=[
                "hv",
                "lv",
                "sn_mva",
                "vn_hv_kv",
                "vn_lv_kv",
                "vkr_percent",
                "vk_percent",
                "pfe_kw",
                "i0_percent",
                "index",
            ],
        )
        self.transformadores_df = pd.concat(
            [self.transformadores_df, novo_trafo], ignore_index=True
        )

    def adicionar_carga(self, barra: str, p_mw: float, q_mvar: float):
        """Adiciona uma carga manualmente."""
        nova_carga = pd.DataFrame(
            [[barra, p_mw, q_mvar, None]], columns=["barra", "p_mw", "q_mvar", "index"]
        )
        self.cargas_df = pd.concat([self.cargas_df, nova_carga], ignore_index=True)

    def definir_rede_externa(self, barra: str, vm_pu: float = 1.0):
        """Define a barra como referência (external grid)."""
        self.rede_externa = {"barra": barra, "vm_pu": vm_pu}

    def criar_rede(self):
        """Constrói a rede no pandapower a partir dos DataFrames."""
        # Mapeamento nome_barra -> índice
        barra_para_idx = {}

        # Criar barras
        for i, row in self.barras_df.iterrows():
            idx = pp.create_bus(self.net, name=row["nome"], vn_kv=row["vn_kv"])
            barra_para_idx[row["nome"]] = idx
            self.barras_df.at[i, "index"] = idx

        # Criar rede externa (deve ser antes das linhas/trafos para conectividade)
        if self.rede_externa:
            nome_ext = self.rede_externa["barra"]
            if nome_ext in barra_para_idx:
                pp.create_ext_grid(
                    self.net,
                    bus=barra_para_idx[nome_ext],
                    vm_pu=self.rede_externa.get("vm_pu", 1.0),
                )
            else:
                raise ValueError(f"Barra '{nome_ext}' da rede externa não encontrada.")

        # Criar linhas
        for i, row in self.linhas_df.iterrows():
            from_idx = barra_para_idx.get(row["de"])
            to_idx = barra_para_idx.get(row["para"])
            if from_idx is None or to_idx is None:
                raise ValueError(
                    f"Barra de origem ou destino da linha não encontrada: {row['de']} -> {row['para']}"
                )
            idx = pp.create_line(
                self.net,
                from_bus=from_idx,
                to_bus=to_idx,
                length_km=row["comprimento_km"],
                std_type=row["std_type"],
                name=f"L{row['de']}-{row['para']}",
            )
            self.linhas_df.at[i, "index"] = idx

        # Criar transformadores
        for i, row in self.transformadores_df.iterrows():
            hv_idx = barra_para_idx.get(row["hv"])
            lv_idx = barra_para_idx.get(row["lv"])
            if hv_idx is None or lv_idx is None:
                raise ValueError(
                    f"Barra HV ou LV do transformador não encontrada: {row['hv']} -> {row['lv']}"
                )
            idx = pp.create_transformer_from_parameters(
                self.net,
                hv_bus=hv_idx,
                lv_bus=lv_idx,
                sn_mva=row["sn_mva"],
                vn_hv_kv=row["vn_hv_kv"],
                vn_lv_kv=row["vn_lv_kv"],
                vkr_percent=row["vkr_percent"],
                vk_percent=row["vk_percent"],
                pfe_kw=row["pfe_kw"],
                i0_percent=row["i0_percent"],
                name=f"T{row['hv']}-{row['lv']}",
            )
            self.transformadores_df.at[i, "index"] = idx

        # Criar cargas
        for i, row in self.cargas_df.iterrows():
            barra_idx = barra_para_idx.get(row["barra"])
            if barra_idx is None:
                raise ValueError(f"Barra da carga não encontrada: {row['barra']}")
            idx = pp.create_load(
                self.net,
                bus=barra_idx,
                p_mw=row["p_mw"],
                q_mvar=row["q_mvar"],
                name=f"Carga_{row['barra']}",
            )
            self.cargas_df.at[i, "index"] = idx

        print("Rede criada com sucesso no pandapower.")

    def plotar_diagrama(self, arquivo_saida: Optional[str] = None):
        """
        Desenha o diagrama unifilar usando schemdraw.
        Necessário que as barras tenham coordenadas (x, y).
        """
        # Verificar se as coordenadas estão presentes
        if self.barras_df[["x", "y"]].isnull().any().any():
            raise ValueError(
                "Todas as barras precisam de coordenadas (x, y) para plotagem."
            )

        # Mapear nome -> (x, y)
        posicoes = {
            row["nome"]: (row["x"], row["y"]) for _, row in self.barras_df.iterrows()
        }

        with schemdraw.Drawing(file=arquivo_saida, show=True) as d:
            # Desenhar barras (como pontos ou círculos)
            elementos_barra = {}
            for nome, (x, y) in posicoes.items():
                # Desenha um pequeno círculo para a barra
                el = (
                    elm.Dot(open=True).at((x, y)).label(nome, fontsize=10, loc="bottom")
                )
                elementos_barra[nome] = el

            # Desenhar linhas (conexões entre barras)
            for _, row in self.linhas_df.iterrows():
                de = row["de"]
                para = row["para"]
                if de in elementos_barra and para in elementos_barra:
                    # Obter posições
                    x1, y1 = posicoes[de]
                    x2, y2 = posicoes[para]
                    # Desenha linha com um pequeno texto para o comprimento
                    linha = elm.Line().at((x1, y1)).to((x2, y2))
                    # Adicionar label com comprimento no meio da linha
                    meio_x = (x1 + x2) / 2
                    meio_y = (y1 + y2) / 2
                    d.add(elm.Line().at((x1, y1)).to((x2, y2)))
                    d.add(
                        elm.Dot(open=True, fill="none")
                        .at((meio_x, meio_y))
                        .label(f"{row['comprimento_km']} km", fontsize=8)
                    )
                else:
                    print(
                        f"Aviso: Linha entre {de} e {para} não pode ser desenhada (coordenadas ausentes)."
                    )

            # Desenhar transformadores (como dois círculos ou símbolo de transformador)
            for _, row in self.transformadores_df.iterrows():
                hv = row["hv"]
                lv = row["lv"]
                if hv in posicoes and lv in posicoes:
                    x1, y1 = posicoes[hv]
                    x2, y2 = posicoes[lv]
                    # Desenha um transformador simplificado (círculo com dois terminais)
                    # Pode-se usar elm.Transformer, mas ele precisa de posicionamento.
                    # Para simplificar, desenhamos uma linha tracejada com um círculo no meio.
                    d.add(elm.Line().at((x1, y1)).to((x2, y2)).linestyle("--"))
                    meio_x = (x1 + x2) / 2
                    meio_y = (y1 + y2) / 2
                    d.add(
                        elm.Dot(open=False, fill="white")
                        .at((meio_x, meio_y))
                        .label("T", fontsize=10)
                    )
                else:
                    print(
                        f"Aviso: Transformador entre {hv} e {lv} não pode ser desenhado."
                    )

            # Desenhar cargas (como setas ou resistores)
            for _, row in self.cargas_df.iterrows():
                barra = row["barra"]
                if barra in posicoes:
                    x, y = posicoes[barra]
                    # Colocar um resistor pequeno ao lado da barra (deslocado)
                    d.add(
                        elm.Resistor()
                        .at((x + 0.3, y - 0.3))
                        .label(f"{row['p_mw']} MW", fontsize=8)
                        .right()
                    )
                else:
                    print(f"Aviso: Carga na barra {barra} não pode ser desenhada.")

            # Indicar rede externa
            if self.rede_externa:
                barra_ext = self.rede_externa["barra"]
                if barra_ext in posicoes:
                    x, y = posicoes[barra_ext]
                    d.add(elm.SourceV().at((x - 0.5, y + 0.5)).label("Ext", fontsize=8))

    def resolver_fluxo_potencia(self):
        """Executa o fluxo de potência e exibe resultados."""
        pp.runpp(self.net)
        print("\n--- Resultado do Fluxo de Potência ---")
        print(self.net.res_bus[["vm_pu", "va_degree", "p_mw", "q_mvar"]])
        return self.net.res_bus
