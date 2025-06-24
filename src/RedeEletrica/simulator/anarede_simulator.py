import pandas as pd
import re

def read_dataset_anarede(filepath):
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    section_pattern = re.compile(r"^(DBAR|DLIN|DGLT|DARE|DGBT)\s*$")
    end_pattern = re.compile(r"^99999")
    tables = {}
    current_section = None
    current_header = []
    current_data = []

    def save_table():
        if current_section and current_header and current_data:
            adjusted_data = []
            for row in current_data:
                if len(row) < len(current_header):
                    row = row + [""] * (len(current_header) - len(row))
                elif len(row) > len(current_header):
                    row = row[:len(current_header)]
                adjusted_data.append(row)
            df = pd.DataFrame(adjusted_data, columns=current_header)
            tables[current_section] = df

    for line in lines:
        line = line.rstrip("\n")
        section_match = section_pattern.match(line)
        if section_match:
            save_table()
            current_section = section_match.group(1)
            current_header = []
            current_data = []
            continue

        if current_section:
            if not current_header and line.startswith("("):
                header = re.findall(r"\(([^)]+)\)", line)
                current_header = [h.strip() for h in header]
                continue
            if end_pattern.match(line):
                save_table()
                current_section = None
                current_header = []
                current_data = []
                continue
            if line.strip() and not line.startswith("("):
                row = re.split(r'\s{2,}', line.strip())
                current_data.append(row)

    # Salva a última tabela se necessário
    save_table()
    return tables



# Exemplo de uso:
dfs = read_dataset_anarede(r"C:\Users\pedrovictor.veras\Documents\GitHub\Repopulation-With-Elite-Set\src\RedeEletrica\assets\CASO_FBA100.txt")

print("Tabelas lidas:")
for key, df in dfs.items():
    print(f"{key}:")
    print(df.head(), "\n")  # Exibe as primeiras linhas de cada DataFrame
    

print("DataFrames lidos:")
print(dfs["DBAR"])
print(dfs["DLIN"])