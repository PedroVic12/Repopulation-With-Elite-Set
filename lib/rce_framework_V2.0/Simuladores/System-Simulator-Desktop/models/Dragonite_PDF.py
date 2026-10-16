from PyPDF2 import PdfReader, PdfFileWriter, PdfFileReader
import os
import pandas as pd
import re
from PIL import Image
from deep_translator import GoogleTranslator
from langdetect import detect


class Dragonite:
    def __init__(self, path):
        self.reader = PdfReader(path)
        self.number_of_pages = len(self.reader.pages)



    #! Metodos de tradução
    def traduzirTexto(self, texto_em_ingles):
        texto_traduzido = GoogleTranslator(source='en', target='pt').translate(texto_em_ingles) # use translate_text here
        return texto_traduzido
    
    def is_english(self, text):
        try:
            # Se detectar que o idioma é inglês, retorna True
            return detect(text) == 'en'
        except:
            return False

    def maybe_translate(self, text):
        # Verifica se o texto é em inglês
        if self.is_english(text):
            
            # Traduz o texto
            print('\n\n\nTraduzindo texto...')
            return self.traduzirTexto(text)
        # Retorna o texto original se não for inglês
        return text

    #!Metodos PDF
    def split_pdf(self, output_directory="./"):
        """
        Split the original PDF into multiple one-page PDFs.
        """
        if not output_directory.endswith("/"):
            output_directory += "/"

        inputpdf = PdfFileReader(open(self.reader.stream.name, "rb"))
        for i in range(inputpdf.numPages):
            output = PdfFileWriter()
            output.addPage(inputpdf.getPage(i))
            with open(output_directory + f"pdf_{i+1}.pdf", "wb") as output_stream:
                output.write(output_stream)

        return [output_directory + f"pdf_{i+1}.pdf" for i in range(inputpdf.numPages)]

    def pdf_to_image(self, pdf_path, output_directory="./"):
        """
        Convert a PDF file to JPEG images.
        """
        if not output_directory.endswith("/"):
            output_directory += "/"

        # Convert PDF to images
        images = Image.open(pdf_path)
        image_paths = []
        for i, image in enumerate(images):
            image_path = output_directory + f"image_{i+1}.jpeg"
            image.save(image_path, "JPEG")
            image_paths.append(image_path)

        return image_paths

    def ler_pagina(self, page_number):
        page_number -= 1
        if 0 <= page_number < self.number_of_pages:
            return self.reader.pages[page_number].extract_text()
        else:
            return None

    def ler_intervalo_paginas(self, inicio, fim):
        """
        Lê um intervalo de páginas do PDF e retorna o texto concatenado.

        :param inicio: Número da página inicial.
        :param fim: Número da página final.
        :return: Texto concatenado das páginas.
        """
        texto_total = ""
        for pagina in range(inicio, fim+1):  # fim+1 para incluir a última página no intervalo
            texto_total += self.ler_pagina(pagina)
        return texto_total
    
    
    #! Métodos Regex

    """
    A função split_text é usada para dividir o texto por equipamento, mas parece que está fazendo a divisão com base no caractere '\n' apenas.
    A função group_by_equipment parece ser onde a mágica acontece. Ela tenta agrupar as informações por equipamento.
    """

    def find_start_P(self, texto_string):
        matches = re.findall(r'^\s*\(P\).*', texto_string, re.MULTILINE)
        return matches

    def find_end_P(self, texto_string):
        matches = re.findall(r'^.*\(P\)\s*$', texto_string, re.MULTILINE)
        return matches

    #! MetodosPandas

    def concatenate_dataframes(self, df_list, axis=0, reset_index=True):
        """
        Concatena uma lista de DataFrames ao longo de um eixo especificado.

        Parâmetros:
        - df_list: Lista de DataFrames para concatenar.
        - axis: Eixo ao longo do qual os DataFrames devem ser concatenados.
                0 para vertical (default) e 1 para horizontal.
        - reset_index: Se True, redefine o índice do DataFrame resultante. Default é True.

        Retorna:
        - DataFrame concatenado.
        """
        concatenated_df = pd.concat(df_list, axis=axis)

        if reset_index and axis == 0:
            concatenated_df = concatenated_df.reset_index(drop=True)

        return concatenated_df


    #! Métodos REGEX
    def criar_dataframeSeguranca(self, texto):
        data = {}
        
        # Splitting the provided text to find all occurrences of "Medidas de Segurança" or "Medidas de segurança"
        split_text = re.split(r'Medidas de [Ss]egurança:', texto)
        
        for idx, section in enumerate(split_text[1:], start=1):  # skip the 0th index as it's before the first occurrence
            # Extracting information until the next occurrence of "Medidas de Segurança:" or other stopping patterns
            extracted_info = re.search(r'(.*?)(?=\d{9}|Ações de [Mm]anutenção:|Medidas de [Ss]egurança:|$)', section, re.DOTALL)
            
            if extracted_info:
                key = f'Medidas de segurança {idx}' if len(split_text) > 2 else 'Medidas de segurança 1'
                data[key] = [extracted_info.group(1).strip()]
        
        # Convert the data dictionary to a DataFrame
        df = pd.DataFrame(data)
        
        return df
    
    
    def criar_dataframeManutencao(self,texto):
        data = {}
        
        # Splitting the provided text to find all occurrences of "Ações de manutenção"
        split_text = texto.split("Ações de manutenção:")
        
        for idx, section in enumerate(split_text[1:], start=1):  # skip the 0th index as it's before the first occurrence
            # Extracting information until the next occurrence of "Ações de manutenção:" or other stopping patterns
            extracted_info = re.search(r'(.*?)(?=\d{9}|Ações de manutenção:|Medidas de [Ss]egurança:)', section, re.DOTALL)
            
            if extracted_info:
                key = f'Ações de manutenção {idx}' if len(split_text) > 2 else 'Ações de manutenção 1'
                data[key] = [extracted_info.group(1).strip()]
        
        # Convert the data dictionary to a DataFrame
        df = pd.DataFrame(data)
        
        return df
    

    def mostrar_matches(self,texto_string):
        """
        Mostra os matches e os textos extraídos para cada padrão de regex.
        """

        # Padrão de regex para extrair informações
        pattern_nome = re.compile(r'(?<=\dHrs ).+?(?=\n\d{10}|\n\(|\n[A-Z])', re.DOTALL)
        pattern_numero_tarefa = re.compile(r'^\d{10}', re.MULTILINE)
        pattern_carencia = re.compile(r'(?<=\d{10} )\d{1,2}')
        pattern_intervalo = re.compile(r'\d+\.\d+(MONTHS|Hours)')
        pattern_relogio = re.compile(r'\d+Hrs')

        # Encontrar todas as correspondências no texto
        matches_nome = [match.group().replace("\n", " ") for match in pattern_nome.finditer(texto_string)]
        matches_numero_tarefa = pattern_numero_tarefa.findall(texto_string)
        matches_carencia = pattern_carencia.findall(texto_string)
        matches_intervalo = pattern_intervalo.findall(texto_string)
        matches_relogio = pattern_relogio.findall(texto_string)

        # Criando o DataFrame
        df = pd.DataFrame({
            'Nome Match': matches_nome,
            'Número da Tarefa Match': matches_numero_tarefa,
            'Intervalo Match': matches_intervalo,
            'Carência Match': matches_carencia,
            'Relógio Match': matches_relogio
        })

        return df


    
    def extrair_periodicidade(self, texto_string):
        """
        Extraia informações específicas do texto fornecido e retorne um dicionário com DataFrames 
        para cada tipo de periodicidade: 'Inspection', 'Drydock', 'Sampling'.
        """
        # Listas para armazenar os dados extraídos
        numero_tarefa = []
        carencia = []
        intervalo = []
        relogio = []
        nome = []

        # Dividindo o texto fornecido em linhas
        lines = texto_string.split("\n")

        # Iterando pelas linhas para extrair dados
        for i in range(len(lines)):
            # Verificar linhas que começam com o padrão de 'Número da Tarefa'
            if re.match(r'^\d{10}', lines[i]):
                numero_tarefa.append(re.search(r'^\d{10}', lines[i]).group())
                carencia.append(re.search(r'^\d{10} (\d{1,2})', lines[i]).group(1))
                intervalo.append(re.search(r'(\d+\.\d+(MONTHS|Hours))', lines[i]).group(1))
                relogio.append(re.search(r'(\d+Hrs)', lines[i]).group(1))
                nome.append(lines[i+1] + " " + lines[i+2])

        # Criando o DataFrame principal
        df = pd.DataFrame({
            'Nome': nome,
            'Número da Tarefa': numero_tarefa,
            'Intervalo': intervalo,
            'Carência': carencia,
            'Relógio': relogio
        })

        # Criando um dicionário para armazenar os DataFrames para cada tipo de periodicidade
        periodicidade_colunas = ['Inspection', 'Drydock', 'Sampling']
        df_dict = {}
        for periodicidade in periodicidade_colunas:
            df_dict[periodicidade] = df[df["Nome"].str.contains(periodicidade)]

        return df_dict
    
    def combinar_periodicidade(self, df1, df2, new_names=('Periodicidade 1', 'Periodicidade 2')):
        """
        Renomeia a coluna 'Nome' e concatena dois DataFrames lado a lado.
        
        Parâmetros:
        - df1: Primeiro DataFrame.
        - df2: Segundo DataFrame.
        - new_names: Nomes novos para a coluna 'Nome' em df1 e df2.

        Retorna:
        - DataFrame resultante da concatenação.
        """
        
        # Renomeando colunas
        df1 = df1.rename(columns={'Nome Match': new_names[0]})
        df2 = df2.rename(columns={'Nome Match': new_names[1]})
        
        # Resetando os índices para alinhar os DataFrames corretamente
        df1 = df1.reset_index(drop=True)
        df2 = df2.reset_index(drop=True)
        
        # Juntando DataFrames lado a lado
        combined_df = pd.concat([df1, df2], axis=1)
        
        return combined_df

    

    def consolidate_columns(self,df):
        # Identify duplicate columns based on column names
        duplicate_columns = df.columns[df.columns.duplicated()].unique()

        # Consolidate duplicate columns
        for col in duplicate_columns:
            # Get all columns with the same name
            duplicate_cols = [duplicate_col for duplicate_col in df if duplicate_col == col]
            
            # Combine columns into a single column
            combined_col = df[duplicate_cols].apply(lambda row: ''.join(row.dropna().astype(str)), axis=1)
            
            # Drop the original duplicate columns and add the combined column
            df = df.drop(columns=duplicate_cols)
            df[col] = combined_col

        return df
    
    def limpar_dataframe(self, df):
        # 1. Drop duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]

        # 2. Drop rows with all NaN values
        df = df.dropna(how='all')

        # 3. Split multi-entry rows into separate rows
        df = self.consolidate_columns(df)

        # 4. Reset index for cleanliness
        df = df.reset_index(drop=True)

        return df





    #! metodos de extrair info
    def find_start_index(self, lines, word):
        for i in range(len(lines)):
            if word in lines[i]:
                return i + 1
        return -1

    def extract_data(self, lines, start_idx):
        data = []
        i = start_idx
        while i < len(lines) and lines[i].strip() != '':
            data.append(lines[i])
            i += 1
        return data

    def split_security_measures(self, text):
        # Dividir o texto em "Medidas de segurança"
        # O primeiro elemento será vazio, então nós o ignoramos
        sections = re.split(r'Medidas de segurança', text)[1:]

        # Para cada seção, obtenha as medidas individuais
        all_measures = [re.findall(r'\d+\) (.+?)\.\n', section)
                        for section in sections]

        # Transpor a lista para ter cada medida de cada seção em uma lista separada
        max_len = max(len(measures) for measures in all_measures)
        measures_transposed = []
        for i in range(max_len):
            row = []
            for measures in all_measures:
                if i < len(measures):
                    row.append(measures[i])
                else:
                    # Se essa seção tiver menos medidas, adicione None
                    row.append(None)
            measures_transposed.append(row)

        # Converta em DataFrame
        df = pd.DataFrame(measures_transposed, columns=[
                          f"Medidas {i+1}" for i in range(len(all_measures))])

        return df


    

    #!Metodos Excel
    def juntar_dataframes(self, list_of_dfs, direcao=1):
        """
        Junta uma lista de DataFrames lado a lado (horizontalmente).
        """
        return pd.concat(list_of_dfs, axis=direcao)

    def add_empty_row(self, df):
        empty_row = pd.DataFrame([[""] * df.shape[1]], columns=df.columns)
        return pd.concat([df, empty_row], ignore_index=True)

    def save_to_excel(self, dfs, sheet_names, filename):
        """
        Salva uma lista de DataFrames em um único arquivo Excel com múltiplas abas.

        Parameters:
        - dfs: Lista de DataFrames
        - sheet_names: Lista de nomes para as abas
        - filename: Nome do arquivo Excel de saída
        """
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for df, sheet_name in zip(dfs, sheet_names):
                df_with_empty_row = self.add_empty_row(df)
                df_with_empty_row.to_excel(
                    writer, sheet_name=sheet_name, index=False)
        print(f'Arquivo excel salvo: {filename}')

    def extrair_nome_aba(self, texto_string):
        """
        Encontra o nome da aba que termina com '(P)' e retorna.
        """
        match = re.search(r'(.+? \(P\))', texto_string)
        if match:
            return match.group(1)
        else:
            return "DefaultSheetName"

    def nome_arquivo_excel(self, pdf_filename):
        """
        Transforma o nome do arquivo PDF no nome desejado para o arquivo Excel.
        """
        base_name = os.path.basename(
            pdf_filename)  # Pega o nome do arquivo sem o caminho
        name_without_extension = os.path.splitext(
            base_name)[0]  # Remove a extensão
        # Transforma "SJ - SAGITARIUS 2023-07-21" em "SAGITARIUS 2023-07-21"
        return name_without_extension.replace("SJ - ", "") + ".xlsx"