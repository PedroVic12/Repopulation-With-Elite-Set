import pandas as pd
import re
import fitz

# ===============================================================
# CLASSE: ETLRepository (MODEL - Camada de Acesso a Dados)
# ===============================================================

class ETLRepository:
    """Gerencia a lógica de Extração de dados de baixo nível para documentos PDF."""

    def __init__(self):
        """Inicializa o ETLRepository."""
        pass


    def extract_text_from_txt(self, filename):
        """
        Lê todo o texto de um arquivo .txt do caminho especificado e retorna como string.

        Args:
            filename (str): O caminho do arquivo .txt a ser lido.

        Returns:
            str: O texto extraído do arquivo.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                text = file.read()
            return text
        except Exception as e:
            print(f"Erro ao ler o arquivo TXT '{filename}': {e}")
            return ""

    def extract_text_from_pdf(self, pdf_path, page_range=None):
        """
        Extrai texto de um arquivo PDF, opcionalmente limitando a um intervalo de páginas.

        Args:
            pdf_path (str): O caminho para o arquivo PDF.
            page_range (list, optional): Uma lista de índices de páginas (base 0) a serem processadas. Se None, todas as páginas são processadas. Defaults to None.

        Returns:
            str: O texto concatenado das páginas extraídas, com marcadores de página.
        """
        doc = fitz.open(pdf_path)
        full_text = ""
        
        # Determina as páginas a serem processadas
        if page_range is None:
            pages_to_process = range(len(doc))
        else:
            # Filtra páginas para garantir que estão dentro do limite do documento
            pages_to_process = [p for p in page_range if p < len(doc)]
        
        for page_num in pages_to_process:
            page = doc.load_page(page_num)
            full_text += f"\n--- Página {page_num + 1} ---\n" # Adiciona marcador de página
            full_text += page.get_text()
        
        doc.close()
        return full_text

    def _clean_contingency_name(self, contingency_name, add_lt_option, prev_part_ends_with_lt=False):
        """
        Limpa e padroniza o nome de uma contingência, removendo termos desnecessários e adicionando 'LT' se aplicável.

        Args:
            contingency_name (str): O nome original da contingência.
            add_lt_option (bool): Se True, tenta adicionar 'LT' se 'kV' estiver presente e 'LT' não for duplicado.
            prev_part_ends_with_lt (bool, optional): Indica se a parte anterior da contingência (em caso de múltiplas) termina com 'LT'. Usado para evitar duplicação. Defaults to False.

        Returns:
            str: O nome da contingência limpo e padronizado.
        """
        # Remove o texto "Contingência Dupla" e variações (ex: "Contingência Dupla da", "Contingência Dupla das")
        cleaned_name = re.sub(r'Contingência Dupla (da|das)?\s*', '', contingency_name, flags=re.IGNORECASE).strip()
        
        # Adiciona "LT" se necessário, evitando duplicações e garantindo formato
        if add_lt_option:
            if not cleaned_name.startswith('LT ') and ' kV ' in cleaned_name:
                # Se não começa com 'LT ' e contém ' kV ', adiciona 'LT '
                cleaned_name = 'LT ' + cleaned_name
            elif cleaned_name.startswith('LT LT '):
                # Corrige caso haja "LT LT " duplicado no início
                cleaned_name = cleaned_name.replace('LT LT ', 'LT ')
            elif prev_part_ends_with_lt and cleaned_name.startswith('LT '):
                # Remove 'LT ' duplicado se a parte anterior já terminou com 'LT'
                cleaned_name = cleaned_name[3:].strip() # Remove apenas o primeiro 'LT ' 
        return cleaned_name

    def _parse_contingency_line(self, contingency_raw_line, process_options, prazo_atual, enable_regex_processing):
        """
        Processa uma linha de texto bruta identificada como contingência, extraindo os detalhes.
        Encapsula a lógica de identificação e separação de contingências duplas.

        Args:
            contingency_raw_line (str): A linha de texto da contingência (ex: '• Contingência Dupla LT X e LT Y').
            process_options (dict): Opções de processamento, como 'separar_duplas' e 'adicionar_lt'.
            prazo_atual (str): O prazo atual (Curto Prazo ou Médio Prazo).
            enable_regex_processing (bool, optional): Se True, ativa o processamento de regex para contingências duplas.

        Returns:
            list: Uma lista de dicionários, onde cada dicionário representa uma contingência extraída.
        """
        contingencias_data = []
        contingencia_base = contingency_raw_line.replace('•', '').replace('-', '').strip() # Garante que a linha bruta seja limpa de marcadores e espaços
        futura = "SIM" if prazo_atual == "Curto Prazo" else "NÃO"

        add_lt_enabled = process_options['adicionar_lt']
        separate_duplas_enabled = process_options['separar_duplas']

        print(f"DEBUG _parse_contingency_line: Raw: '{contingency_raw_line}', Base: '{contingencia_base}', LT_Enabled: {add_lt_enabled}, Sep_Enabled: {separate_duplas_enabled}, Regex_Enabled: {enable_regex_processing}")

        try:
            if enable_regex_processing:
                is_contingencia_dupla = re.search(r'contingência dupla', contingencia_base, re.IGNORECASE)

                if is_contingencia_dupla and separate_duplas_enabled:
                    contingencia_processada = re.sub(r'Contingência Dupla (da|das)?\s*', '', contingencia_base, flags=re.IGNORECASE).strip()
                    print(f"DEBUG _parse_contingency_line: É dupla e separar ativado. Processada: '{contingencia_processada}'")

                    if ' e ' in contingencia_processada:
                        partes = contingencia_processada.split(' e ')
                        print(f"DEBUG _parse_contingency_line: Partes: {partes}")
                        for i, parte in enumerate(partes):
                            parte = parte.strip()
                            prev_part_ends_with_lt = (i > 0 and partes[i-1].strip().endswith('LT'))
                            
                            final_part_name = parte # Valor padrão antes de aplicar a lógica de LT
                            if add_lt_enabled:
                                final_part_name = self._clean_contingency_name(parte, True, prev_part_ends_with_lt)

                            if final_part_name:
                                contingencias_data.append({
                                    'Perda Dupla': final_part_name,
                                    'Futura': futura,
                                    'Perdas Duplas na mesma contigencia': 'SIM'
                                })
                    else:
                        # É uma "Contingência Dupla" mas não tem separador " e ", trata como uma única
                        final_contingency_name = contingencia_processada
                        if add_lt_enabled:
                            final_contingency_name = self._clean_contingency_name(contingencia_processada, True)

                        if final_contingency_name:
                            contingencias_data.append({
                                'Perda Dupla': final_contingency_name,
                                'Futura': futura,
                                'Perdas Duplas na mesma contigencia': 'NÃO'
                            })
                else:
                    # Não é uma "Contingência Dupla" ou a opção de separar está desativada
                    # Trata a linha como uma única contingência, aplicando _clean_contingency_name com add_lt_enabled
                    final_contingency_name = contingencia_base # Valor padrão antes de aplicar a lógica de LT
                    print(f"DEBUG _parse_contingency_line: Não é dupla ou separar desativado. Final Contingency Name base: '{final_contingency_name}'")
                    if add_lt_enabled:
                        final_contingency_name = self._clean_contingency_name(contingencia_base, True)

                    if final_contingency_name:
                        contingencias_data.append({
                            'Perda Dupla': final_contingency_name,
                            'Futura': futura,
                            'Perdas Duplas na mesma contigencia': 'NÃO'
                        })
            else:
                # enable_regex_processing está desativado
                contingencia_bruta_limpa = contingency_raw_line.replace('•', '').replace('-', '').replace('Contingência dupla da', '').strip()
                print(f"DEBUG _parse_contingency_line: Regex desativado. Bruta limpa: '{contingencia_bruta_limpa}'")
                
                final_contingency_name = contingencia_bruta_limpa # Valor padrão antes de aplicar a lógica de LT
                if add_lt_enabled:
                    final_contingency_name = self._clean_contingency_name(contingencia_bruta_limpa, True, False)
                
                if final_contingency_name:
                    contingencias_data.append({
                        'Perda Dupla': final_contingency_name,
                        'Futura': futura,
                        'Perdas Duplas na mesma contigencia': 'NÃO'
                    })
        except Exception as e:
            print(f"ERRO em _parse_contingency_line: {e} para a linha: '{contingency_raw_line}'")
            # Se houver erro, ainda podemos adicionar uma entrada para não travar o processo principal
            contingencias_data.append({
                'Perda Dupla': f"ERRO: {str(e)}", 
                'Futura': futura, 
                'Perdas Duplas na mesma contigencia': 'NÃO'
            })
        
        return contingencias_data

# ===============================================================
# CLASSE: ETLController (CONTROLLER - Camada de Lógica de Negócio)
# ===============================================================

class ETLController:
    """Orquestra as operações de ETL, utilizando o ETLRepository para acesso a dados."""

    _DEFAULT_PROCESS_OPTIONS = {
        'enable_volume_area_extraction': True,
        'enable_prazo_extraction': True,    
        'enable_contingency_identification': True,

        'enable_regex_processing': False,
        'separar_duplas': True,
        'adicionar_lt': True,

        'standardize_columns': True, 

    }

    _COLUMN_NAMES = [
        'Volume',
        'Área Geoelétrica',
        'Perda Dupla',
        'Prazo',
        'Futura',
        'Perdas Duplas na mesma contigencia',
        'Página' # Nova coluna para o número da página
    ]

    def __init__(self):
        """Inicializa o ETLController e seu repositório de dados."""
        self._etl_repository = ETLRepository()
        self.process_options = self._DEFAULT_PROCESS_OPTIONS.copy()

    def extract_pdf_text(self, pdf_path, page_range=None):
        """
        Extrai texto de um arquivo PDF usando o ETLRepository.

        Args:
            pdf_path (str): O caminho para o arquivo PDF.
            page_range (list, optional): Uma lista de índices de páginas (base 0) a serem processadas. Se None, todas as páginas são processadas. Defaults to None.

        Returns:
            str: O texto concatenado das páginas extraídas.
        """
        return self._etl_repository.extract_text_from_pdf(pdf_path, page_range)

    def process_outro_script(self, texto):
        """
        Função placeholder para outros scripts de processamento.
        Retorna um DataFrame de exemplo.

        Args:
            texto (str): O texto a ser processado.

        Returns:
            pd.DataFrame: DataFrame de exemplo.
        """
        return pd.DataFrame({"Exemplo": ["Script 2 em desenvolvimento"]})

    def process_contingencias_duplas(self, texto):
        """
        Processa o texto extraído do PDF para identificar e tabular contingências duplas.

        Args:
            texto (str): O texto completo extraído do PDF.

        Returns:
            pd.DataFrame: Um DataFrame contendo as contingências identificadas e seus atributos.
        """
        try:
            dados = []
            volume_atual = None
            area_geoelerica_atual = None
            prazo_atual = None
            pagina_atual = None # Nova variável para rastrear a página atual

            #! 1) Itera sobre cada linha do texto para extrair informações
            for linha in texto.strip().split('\n'):
                linha = linha.strip()
            
                # Ignora linhas vazias ou marcadores de página
                if not linha:
                    continue
                
                # 1.1) Detecta o marcador de página e atualiza pagina_atual
                if linha.startswith('--- Página'):
                    match_pagina = re.search(r'--- Página (\d+) ---', linha)
                    if match_pagina:
                        pagina_atual = int(match_pagina.group(1))
                    print(f"Marcador de página: {linha}")
                    # Não usar 'continue' aqui para permitir que Volume/Área/Prazo sejam resetados ou usados
                
                # 2) Identifica Volume e Área Geoelétrica
                # Ajustado para aceitar prefixos numéricos (ex: "2.1") e capturar "Volume X - Área Y"
                if self.process_options['enable_volume_area_extraction']:
                    match_volume = re.search(r'(?:\d+\.\d+\s+)?Volume\s*(\d+)\s*[-–]\s*(.+)', linha) # Regex corrigida
                    if match_volume:
                        volume_atual = f"Volume {match_volume.group(1)}"
                        area_geoelerica_atual = match_volume.group(2).strip()
                        continue # Continua para a próxima linha após identificar Volume/Área
                
                # 3) Identifica Prazo (Curto Prazo ou Médio Prazo)
                # Ajustado para capturar Prazo em qualquer parte da linha, case-insensitive, com ou sem número de seção
                if self.process_options['enable_prazo_extraction']:
                    match_prazo = re.search(r'(Curto\s+Prazo|Médio\s+Prazo)', linha, re.IGNORECASE) # Regex corrigida
                    if match_prazo:
                        prazo_atual = match_prazo.group(1).title()
                        continue # Continua para a próxima linha após identificar Prazo

                # 4) Identifica perdas duplas
                # Condição expandida para incluir linhas que começam com 'LT' e contêm 'kV'
                if self.process_options['enable_contingency_identification']:
                    # Regex para identificar linhas de contingência mais robusta
                    if linha.startswith('•') or linha.startswith('-') or re.search(r'Contingência dupla da', linha, re.IGNORECASE) or re.search(r'LT \d+\s*kV', linha):

                        # Delega o processamento detalhado da linha de contingência ao ETLRepository
                        contingencias_processadas = self._etl_repository._parse_contingency_line(
                            linha, self.process_options, prazo_atual, self.process_options['enable_regex_processing']
                        )

                        for c_data in contingencias_processadas:
                            # Garante que todos os dados necessários estão presentes e usa nomes de coluna padronizados
                            dados_linha = {
                                self._COLUMN_NAMES[0]: volume_atual,
                                self._COLUMN_NAMES[1]: area_geoelerica_atual,
                                self._COLUMN_NAMES[2]: c_data['Perda Dupla'],
                                self._COLUMN_NAMES[3]: prazo_atual,
                                self._COLUMN_NAMES[4]: c_data['Futura'],
                                self._COLUMN_NAMES[5]: c_data['Perdas Duplas na mesma contigencia'],
                                self._COLUMN_NAMES[6]: pagina_atual # Adiciona a página atual
                            }
                            dados.append(dados_linha)
                        continue

            # Cria DataFrame a partir dos dados extraídos
            df = pd.DataFrame(dados)
            
            # Reorganiza e padroniza as colunas do DataFrame
            colunas = self._COLUMN_NAMES 
            if not df.empty:
                df = df[colunas]
                
                # Verifica a opção standardize_columns antes de aplicar
                if self.process_options['standardize_columns']:
                    # Padroniza a capitalização das colunas de texto usando o método privado
                    df = self._standardize_dataframe_text_columns(df, [self._COLUMN_NAMES[0], self._COLUMN_NAMES[1], self._COLUMN_NAMES[2], self._COLUMN_NAMES[3]])
            
                # retirar as linhas em branco que ele leu (string vazia ou apenas espaços)
                df = df[df['Perda Dupla'].astype(str).str.strip().astype(bool)]

                print("Dataframe de resultado atualizado por PVRV (após filtragem de Perda Dupla vazia):")
                
            return df

        except Exception as e:
            print(f"Erro no processamento de contingências duplas: {e}")
            return pd.DataFrame({"Erro": [f"Falha no processamento: {e}"]})

    def _standardize_dataframe_text_columns(self, df, columns_to_standardize):
        """
        Padroniza a capitalização das strings em colunas específicas de um DataFrame para o formato de título.

        Args:
            df (pd.DataFrame): O DataFrame a ser processado.
            columns_to_standardize (list): Uma lista de nomes de colunas cujos valores de string devem ser padronizados.

        Returns:
            pd.DataFrame: O DataFrame com as colunas de texto padronizadas.
        """
        for col in columns_to_standardize:
            # Verifica se a coluna existe e se é do tipo 'object' (geralmente strings)
            if col in df.columns and df[col].dtype == 'object': 
                # Aplica a função .title() a cada string na coluna
                df[col] = df[col].apply(lambda x: x.title() if isinstance(x, str) else x)
        return df

        



# Função de teste para demonstrar o ETL de perdas duplas a partir de texto/arquivo TXT
def run_etl_perdas_duplas(test_file_path=None):
    
    print("\n--- Executa um teste da lógica de ETL para perdas duplas a partir de um arquivo TXT ou texto de exemplo. ---")
    etl_controller = ETLController()

    extracted_text = "" # Inicializa com string vazia

    # Você pode modificar as opções de processamento aqui para testar cenários diferentes
    print("\n--- Opções de processamento ---")
    etl_controller.process_options['enable_volume_area_extraction'] = True
    etl_controller.process_options['enable_prazo_extraction'] = True
    etl_controller.process_options['enable_contingency_identification'] = True
    etl_controller.process_options['enable_regex_processing'] = True  # Alterado
    etl_controller.process_options['separar_duplas'] = False       # Alterado 
    etl_controller.process_options['adicionar_lt'] = False         # Alterado 
    etl_controller.process_options['standardize_columns'] = True
    print(etl_controller.process_options)
    print("\n")


    if test_file_path:
        print(f"Lendo texto do arquivo: {test_file_path}")
        file_content = etl_controller._etl_repository.extract_text_from_txt(test_file_path)
        if file_content:
            extracted_text = file_content
        else:
            print(f"Erro: Não foi possível ler o arquivo TXT {test_file_path}. Não há texto para processar.")
            return # Sai da função se não conseguir ler o arquivo

    # Executa o ETL
    if not extracted_text:
        print("Erro: Nenhuma texto para processar. O arquivo TXT pode estar vazio ou não foi lido.")
        return

    df_resultados = etl_controller.process_contingencias_duplas(extracted_text)
    
    # Exibe os resultados
    print("\n--- Resultados do ETL ---")
    print(df_resultados.head(10)) 
    print("\n--- Teste concluído ---")

if __name__ == '__main__':
    run_etl_perdas_duplas(r'C:\Users\pedrovictor.veras\OneDrive - Operador Nacional do Sistema Eletrico\Documentos\ESTAGIO_ONS_PVRV_2025\GitHub\Palkia-PDF-extractor\src\BulbassaurQT6-ETL\sistema-ferramentas-RPA-desktop\app\controllers\dataset_perdas_duplas.txt')



