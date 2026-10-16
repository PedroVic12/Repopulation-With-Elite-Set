import streamlit as st
import tempfile, os, zipfile, io
from pathlib import Path
import sys

# Adiciona o caminho do projeto onde estão os models Dragonite/Palkia
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

print(project_root)

try:
    from models.Dragonite_PDF import Dragonite
    from models.Palkia_Excel import  Palkia

except Exception as e:
    Dragonite = None
    Palkia = None
    IMPORT_ERROR = e
else:
    IMPORT_ERROR = None

def process_pdf(input_path, start_page, end_page, output_dir, log_cb=print):
    """Processa o PDF usando Dragonite/Palkia e gera Excel por página.
    Retorna dict com created_files e errors.
    """
    if IMPORT_ERROR is not None or Dragonite is None or Palkia is None:
        raise RuntimeError(f"Falha ao importar models Dragonite/Palkia: {IMPORT_ERROR}")

    os.makedirs(output_dir, exist_ok=True)
    created, errors = [], []

    try:
        dragonite = Dragonite(input_path)
        total = int(getattr(dragonite, 'number_of_pages', end_page))
        if end_page > total:
            end_page = total
    except Exception as e:
        raise RuntimeError(f"Não foi possível abrir o PDF: {e}")

    for pagina in range(int(start_page), int(end_page) + 1):
        try:
            log_cb(f"\nPágina {pagina}")
            texto = dragonite.ler_pagina(pagina)

            # Título/planilha
            try:
                titulo_df = dragonite.find_start_P(texto)
                titulo1 = titulo_df[0] if titulo_df else None
            except Exception:
                titulo1 = None

            try:
                equipamento_array = dragonite.find_end_P(texto)
                sheet_name = equipamento_array[0] if equipamento_array else 'Página'
            except Exception:
                sheet_name = 'Página'

            # DataFrames principais
            array_df = []
            try:
                df1 = dragonite.criar_dataframeManutencao(texto)
                array_df.append(df1)
            except Exception as e:
                log_cb(f"- Erro ao extrair Ações de manutenção: {e}")

            try:
                df2 = dragonite.criar_dataframeSeguranca(texto)
                array_df.append(df2)
            except Exception as e:
                log_cb(f"- Erro ao extrair Medidas de segurança: {e}")

            try:
                result_df = dragonite.concatenate_dataframes(array_df, axis=1)
            except Exception as e:
                log_cb(f"- Erro ao concatenar dataframes: {e}")
                result_df = None

            # Criar Excel
            out_file = os.path.join(output_dir, f"template_model_{pagina}.xlsx")
            p = Palkia(nome_arquivo=out_file, sheet_name=sheet_name)

            try:
                # Ajuste do título e mescla
                try:
                    p.clear_worksheet(sheet_name)
                except Exception:
                    pass
                try:
                    p.merge_cells_range(sheet_name, 'A1:F1')
                except Exception:
                    pass
                if titulo1:
                    p.add_title(sheet_name, 'A1', titulo1, font_size=16)
            except Exception as e:
                log_cb(f"- Erro ao configurar título: {e}")

            # Colunas principais (se existirem)
            if result_df is not None and not result_df.empty:
                try:
                    lastRow = p.get_last_row(sheet_name, 'A')
                except Exception:
                    lastRow = 0

                # Ações de manutenção 1
                try:
                    if 'Ações de manutenção 1' in result_df.columns:
                        p.add_dataframe(sheet_name, result_df[['Ações de manutenção 1']], lastRow + 1, 1, color_option='verde_claro')
                    else:
                        log_cb('Coluna ausente: Ações de manutenção 1')
                except Exception as e:
                    log_cb(f"- Erro ao escrever Ações de manutenção 1: {e}")

                # Medidas de segurança 1
                try:
                    if 'Medidas de segurança 1' in result_df.columns:
                        lastRow = p.get_last_row(sheet_name, 'A')
                        p.add_dataframe(sheet_name, result_df[['Medidas de segurança 1']], lastRow + 2, 1, color_option='azul_claro')
                    else:
                        log_cb('Coluna ausente: Medidas de segurança 1')
                except Exception as e:
                    log_cb(f"- Erro ao escrever Medidas de segurança 1: {e}")

            try:
                p.format_columns(sheet_name, 'A', width=25)
                p.format_columns(sheet_name, 'B', 'F', 15)
                p.save()
            except Exception as e:
                log_cb(f"- Erro ao salvar arquivo: {e}")

            created.append(out_file)
            log_cb(f"✔ Gerado: {Path(out_file).name}")
        except Exception as e:
            msg = f"Falha na página {pagina}: {e}"
            errors.append(msg)
            log_cb(f"❌ {msg}")

    return {"created_files": created, "errors": errors}

st.set_page_config(page_title="PDF -> Excel", page_icon="📄", layout="centered")
st.title("PDF → Excel - Painel de Controle")

uploaded = st.file_uploader("Envie o PDF", type=["pdf"])
col1, col2 = st.columns(2)
start_page = col1.number_input("Página inicial", min_value=1, value=66, step=1)
end_page = col2.number_input("Página final", min_value=start_page, value=100, step=1)

run = st.button("Processar")

log_container = st.container()
result_container = st.container()

if run:
    if not uploaded:
        st.warning("Envie um PDF antes de processar.")
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, uploaded.name)
            with open(input_path, "wb") as f:
                f.write(uploaded.read())

            output_dir = os.path.join(tmpdir, "output_excel")
            logs = []

            def log_cb(msg):
                logs.append(str(msg))
                with log_container:
                    st.write(msg)

            with st.status("Processando...", expanded=True) as status:
                try:
                    # Processamento real via models Dragonite/Palkia
                    result = process_pdf(input_path, int(start_page), int(end_page), output_dir, log_cb)
                    status.update(label="Concluído!", state="complete")
                except Exception as e:
                    status.update(label=f"Falhou: {e}", state="error")
                    st.stop()

            created_files = result.get("created_files", [])
            errors = result.get("errors", [])

            # Zip para download
            if created_files:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
                    for fp in created_files:
                        z.write(fp, arcname=os.path.basename(fp))
                zip_buf.seek(0)
                with result_container:
                    st.success(f"{len(created_files)} arquivos gerados.")
                    st.download_button(
                        "Baixar Excel (ZIP)",
                        data=zip_buf,
                        file_name="excel_output.zip",
                        mime="application/zip",
                    )
            if errors:
                with result_container:
                    st.error(f"Ocorreram {len(errors)} erros.")
                    for e in errors:
                        st.write(f"- {e}")