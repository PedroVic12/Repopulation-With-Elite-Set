import pandas as pd
import streamlit as st

# Modelo de dados
class DataModel:
    def __init__(self):
        self._data = None
        self.df = pd.DataFrame()
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value

    def load_excel(self, uploaded_file):
        try:
            self._data = pd.read_excel(uploaded_file, sheet_name=None)
            return True, "Arquivo carregado com sucesso!"
        except Exception as e:
            return False, f"Erro ao carregar arquivo: {e}"
        
    def load_data(self, file):
        try:
            if file is not None:
                if file.name.endswith('.csv'):
                    self.df = pd.read_csv(file)
                elif file.name.endswith(('.xls', '.xlsx')):
                    self.df = pd.read_excel(file)
                else:
                    st.error("Formato de arquivo não suportado. Por favor, envie um arquivo CSV ou Excel.")
                    return False
                return True
            return False
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return False


class DashboardViewModel:
    def __init__(self, model):
        self.model = model
        self._initialize_session_state()
        
    def _initialize_session_state(self):
        if 'show_chat' not in st.session_state:
            st.session_state.show_chat = False
        if 'messages' not in st.session_state:
            st.session_state.messages = []
    
    def get_available_tables(self):
        return list(self.model.data.keys()) if self.model.data else []
    
    def get_table_data(self, table_name):
        return self.model.data[table_name] if self.model.data else None
    
    def calculate_statistics(self, df, column):
        return {
            'min': df[column].min(),
            'max': df[column].max(),
            'mean': df[column].mean(),
            'std': df[column].std()
        }