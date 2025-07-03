# app_streamlit.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

# --- CONTROLADOR (A camada 'C' do Frontend) ---
# Classe que encapsula a lógica de comunicação com a API
class TaskController:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url

    def get_tasks(self):
        try:
            response = requests.get(f"{self.base_url}/tasks")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao conectar com o backend: {e}")
            return []

    def add_task(self, description, category):
        payload = {"description": description, "category": category}
        try:
            response = requests.post(f"{self.base_url}/tasks", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao adicionar tarefa: {e}")
            return None

    def update_task_status(self, task_id, completed):
        payload = {"completed": completed}
        try:
            requests.put(f"{self.base_url}/tasks/{task_id}", json=payload).raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao atualizar tarefa: {e}")

    def delete_task(self, task_id):
        try:
            requests.delete(f"{self.base_url}/tasks/{task_id}").raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao deletar tarefa: {e}")

# --- VISÃO (A camada 'V' e 'M' do Frontend) ---
# A UI e o gerenciamento de estado (st.session_state)

def main_view():
    st.set_page_config(layout="wide", page_title="Todo List com Pomodoro")
    st.title("✅ Todo List com Pomodoro e Categorias")
    st.markdown("Gerencie suas tarefas, foque com o Pomodoro e veja seu progresso!")

    controller = TaskController()
    
    # Gerenciamento de estado (Modelo)
    if 'tasks' not in st.session_state:
        st.session_state.tasks = controller.get_tasks()
    if 'pomodoro_active' not in st.session_state:
        st.session_state.pomodoro_active = False
        st.session_state.pomodoro_task_desc = ""

    # Layout em colunas
    col1, col2 = st.columns([1.2, 1])

    # --- Coluna 1: Gerenciamento de Tarefas ---
    with col1:
        st.header("Gerenciar Tarefas")
        
        # Formulário para adicionar nova tarefa
        with st.form("new_task_form", clear_on_submit=True):
            new_desc = st.text_input("Nova Tarefa:", placeholder="Ex: Estudar Streamlit")
            new_cat = st.selectbox("Categoria:", ["Trabalho", "Estudo", "Pessoal", "Fitness"], index=0)
            submitted = st.form_submit_button("Adicionar Tarefa")
            if submitted and new_desc:
                controller.add_task(new_desc, new_cat)
                st.session_state.tasks = controller.get_tasks() # Recarrega a lista
                st.rerun()

        st.subheader("Minhas Tarefas")
        
        # Filtro de tarefas
        show_completed = st.checkbox("Mostrar tarefas concluídas")
        
        # Lista de tarefas
        tasks_to_show = st.session_state.tasks if show_completed else [t for t in st.session_state.tasks if not t['completed']]
        
        if not tasks_to_show:
            st.info("Nenhuma tarefa pendente. Adicione uma acima!")
        else:
            for task in sorted(tasks_to_show, key=lambda x: x['id']):
                task_id = task['id']
                
                c1, c2, c3, c4 = st.columns([0.1, 0.5, 0.2, 0.2])
                
                with c1:
                    # Checkbox para concluir tarefa
                    completed = st.checkbox("", value=task['completed'], key=f"check_{task_id}")
                    if completed != task['completed']:
                        controller.update_task_status(task_id, completed)
                        st.session_state.tasks = controller.get_tasks()
                        st.rerun()

                with c2:
                    # Descrição e categoria
                    desc_style = "text-decoration: line-through; color: grey;" if task['completed'] else ""
                    st.markdown(f"<span style='{desc_style}'>{task['description']}</span>", unsafe_allow_html=True)
                    st.caption(f"Categoria: {task['category']}")

                with c3:
                    # Botão Pomodoro
                    if not task['completed']:
                        if st.button("🍅 Focar", key=f"focus_{task_id}", use_container_width=True, disabled=st.session_state.pomodoro_active):
                            st.session_state.pomodoro_active = True
                            st.session_state.pomodoro_task_desc = task['description']
                            st.rerun()
                
                with c4:
                    # Botão Deletar
                    if st.button("🗑️ Deletar", key=f"del_{task_id}", use_container_width=True):
                        controller.delete_task(task_id)
                        st.session_state.tasks = controller.get_tasks()
                        st.rerun()
                st.divider()

    # --- Coluna 2: Pomodoro e Gráficos ---
    with col2:
        # Seção do Pomodoro
        st.header("🍅 Timer Pomodoro")
        if st.session_state.pomodoro_active:
            run_pomodoro(st.session_state.pomodoro_task_desc)
        else:
            st.info("Selecione '🍅 Focar' em uma tarefa para iniciar o timer.")

        st.divider()

        # Seção do Gráfico
        st.header("📊 Tarefas por Categoria")
        if st.session_state.tasks:
            df = pd.DataFrame(st.session_state.tasks)
            category_counts = df['category'].value_counts().reset_index()
            category_counts.columns = ['category', 'count']
            
            fig = px.pie(category_counts, names='category', values='count', 
                         title='Distribuição de Tarefas', hole=.3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Nenhuma tarefa para exibir no gráfico.")

def run_pomodoro(task_description, work_minutes=25, break_minutes=5):
    """Função para rodar e exibir o timer Pomodoro."""
    st.success(f"Foco na tarefa: **{task_description}**")
    
    # Placeholders para o timer e barra de progresso
    timer_placeholder = st.empty()
    progress_placeholder = st.empty()

    total_seconds = work_minutes * 60
    for seconds_left in range(total_seconds, -1, -1):
        mins, secs = divmod(seconds_left, 60)
        timer_text = f"{mins:02d}:{secs:02d}"
        timer_placeholder.metric("Tempo Restante", timer_text)
        
        progress = 1.0 - (seconds_left / total_seconds)
        progress_placeholder.progress(progress)
        
        time.sleep(1)

    # Fim do pomodoro
    st.balloons()
    st.success("Pomodoro concluído! Hora de uma pausa de 5 minutos.")
    st.session_state.pomodoro_active = False
    
    # Botão para recomeçar
    if st.button("Fechar Timer"):
        st.rerun()

if __name__ == '__main__':
    main_view()