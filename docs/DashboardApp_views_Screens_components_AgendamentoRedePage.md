# AgendamentoRedePage.py

```python
import streamlit as st
from streamlit_timeline import st_timeline
import pathlib
import json
import datetime
import os

# ==================== CONFIGURAÇÃO DE DIRETÓRIO ====================

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"

# ==================== FUNÇÕES DE UTILIDADE ====================

def listar_runs():
    return sorted([f.name for f in OUTPUT_DIR.iterdir() if f.is_dir() and f.name.startswith("run_")])

def listar_configs(run_dir):
    run_path = OUTPUT_DIR / run_dir
    return sorted([f.name for f in run_path.iterdir() if f.is_dir() and f.name.startswith("config_")])

def listar_execucoes(run_dir, config_dir):
    config_path = OUTPUT_DIR / run_dir / config_dir
    result_files = list(config_path.glob("*_results.json"))
    exec_ids = sorted([
        f.name.split("_exec_")[1].split("_")[0]
        for f in result_files
    ])
    return exec_ids

def carregar_json(run_dir, config_dir, exec_num, tipo):
    filename = f"{config_dir}_exec_{exec_num}_{tipo}.json"
    json_path = OUTPUT_DIR / run_dir / config_dir / filename

    if not json_path.exists():
        st.error(f"Arquivo JSON não encontrado: {json_path}")
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar JSON ({filename}): {e}")
        return None

# ==================== FUNÇÃO PRINCIPAL ====================

def AgendamentoRedePage():
    st.title("🗂️ Visualizador de Agendamentos por Execução")

    # --- Seleção de diretórios ---
    run_dir = st.selectbox("📁 Selecione o diretório de execução:", listar_runs())
    if not run_dir: return

    config_dir = st.selectbox("⚙️ Selecione a configuração:", listar_configs(run_dir))
    if not config_dir: return

    exec_num = st.selectbox("🔢 Selecione a execução:", listar_execucoes(run_dir, config_dir))
    if not exec_num: return

    st.markdown("---")

    # --- Carrega JSONs ---
    results_data = carregar_json(run_dir, config_dir, exec_num, "results")
    vis_data = carregar_json(run_dir, config_dir, exec_num, "visualization")

    if not results_data or not vis_data:
        st.stop()

    # ==================== LAYOUT PRINCIPAL ====================

    col1, col2, col3 = st.columns(3)
    col1.metric("Melhor Fitness", f"{results_data['best_fitness']:.2f}")
    col2.metric("Geração Ótima", results_data['best_gen_idx'])
    col3.metric("Tempo de Execução", results_data['time'])

    st.markdown("### 📌 Variáveis Ótimas")
    st.write(results_data['best_variables'])

    st.markdown("---")
    st.subheader("🕒 Linha do Tempo das Intervenções")

    items = vis_data.get("items", [])

    if not items:
        st.warning("Nenhum item de visualização encontrado.")
        return

    timeline = st_timeline(items, groups=[], options={"height": 300}, key=f"timeline_{config_dir}_{exec_num}")

    if timeline and "id" in timeline:
        st.info(f"Item selecionado: {timeline['id']}")

        # Busca o item correspondente
        item = next((it for it in items if it["id"] == timeline["id"]), None)
        if item:
            st.write("**Conteúdo:**", item.get("content"))
            st.write("**Início:**", item.get("start"))
            st.write("**Fim:**", item.get("end"))
            st.write("**Duração:**", item.get("title"))

    # ========== TABELAS ADICIONAIS ==========
    st.markdown("---")
    st.subheader("📊 Dados Brutos da Visualização")
    st.json(vis_data, expanded=False)

    st.markdown("### 🧪 Parâmetros do Algoritmo")
    st.json(results_data.get("params", {}), expanded=False)


```