import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import calendar
import random
from typing import List, Dict, Any
import os

# Set page configuration
st.set_page_config(
    page_title="Controle de Equipamentos",
    page_icon="🔧",
    layout="wide"
)

# Inject custom CSS to reduce font size of buttons
st.markdown(
    """
    <style>
    div.stButton > button {
        font-size: 0.8rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# MVC Architecture Implementation

# ==================== MODEL ====================
class MaintenanceRecord:
    def __init__(self, id, equipment_id, maintenance_type, date, resolution_days, operator, manager):
        self.id = id
        self.equipment_id = equipment_id
        self.maintenance_type = maintenance_type
        self.date = date
        self.resolution_days = resolution_days
        self.operator = operator
        self.manager = manager

    def to_dict(self):
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'maintenance_type': self.maintenance_type,
            'date': self.date,
            'resolution_days': self.resolution_days,
            'operator': self.operator,
            'manager': self.manager
        }


class Equipment:
    def __init__(self, id, name, sector, installation_date):
        self.id = id
        self.name = name
        self.sector = sector
        self.installation_date = installation_date

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sector': self.sector,
            'installation_date': self.installation_date
        }


class MaintenanceModel:
    def __init__(self):
        self.maintenance_records = []
        self.equipments = []
        self.load_sample_data()

    def load_sample_data(self):
        # Generate sample equipment (more realistic distribution)
        sectors = ["Produção", "Engenharia", "Logística", "Qualidade", "Manutenção"]
        for i in range(1, 350):  # Increased number of equipments
            eq = Equipment(
                id=i,
                name=f"Equipamento {i}",
                sector=random.choice(sectors),
                installation_date=datetime.now() - timedelta(days=random.randint(30, 1800)) # Wider range for installation dates
            )
            self.equipments.append(eq)

        # Generate sample maintenance records (more realistic distribution and volume)
        maintenance_types = [
            "Manutenção Corretiva Não Planejada",
            "Manutenção Corretiva Planejada",
            "Manutenção Preventiva",
            "Manutenção Preditiva",
            "Inspeção de Rotina",
            "Melhoria Contínua",
            "Substituição de Componente"
        ]

        operators = ["Ana", "Bruno", "Carla", "Daniel", "Elisa", "Fábio", "Gisele", "Heitor", "Ingrid", "João"]
        managers = ["Karina", "Lucas", "Mariana", "Nelson", "Olivia"]

        now = datetime.now()

        for i in range(1, 15000):  # Significantly increased number of records
            equipment_id = random.randint(1, len(self.equipments))
            record_date = now - timedelta(days=random.randint(0, 730)) # Records for the last two years
            maintenance_type = random.choice(maintenance_types)

            # More realistic resolution days based on maintenance type
            if "Preventiva" in maintenance_type or "Inspeção" in maintenance_type:
                res_days = round(random.uniform(0.25, 2), 2) # Hours to a couple of days
            elif "Corretiva Não Planejada" in maintenance_type:
                res_days = round(random.uniform(1, 15), 2) # Days to a couple of weeks
            elif "Corretiva Planejada" in maintenance_type or "Substituição" in maintenance_type:
                res_days = round(random.uniform(2, 10), 2)
            elif "Preditiva" in maintenance_type or "Melhoria" in maintenance_type:
                res_days = round(random.uniform(3, 30), 2) # Can take longer

            record = MaintenanceRecord(
                id=i,
                equipment_id=equipment_id,
                maintenance_type=maintenance_type,
                date=record_date,
                resolution_days=res_days,
                operator=random.choice(operators),
                manager=random.choice(managers)
            )
            self.maintenance_records.append(record)

    def get_all_maintenance_records(self):
        return [record.to_dict() for record in self.maintenance_records]

    def get_all_equipments(self):
        return [eq.to_dict() for eq in self.equipments]

    def get_total_maintenance_count(self):
        return len(self.maintenance_records)

    def get_average_resolution_time(self):
        total_days = sum(record.resolution_days for record in self.maintenance_records)
        return round(total_days / len(self.maintenance_records), 2) if self.maintenance_records else 0

    def get_equipment_with_most_occurrences(self):
        equipment_counts = {}
        for record in self.maintenance_records:
            equipment_counts[record.equipment_id] = equipment_counts.get(record.equipment_id, 0) + 1

        if not equipment_counts:
            return None, 0

        max_equipment_id = max(equipment_counts, key=equipment_counts.get)
        return max_equipment_id, equipment_counts[max_equipment_id]

    def get_occurrences_by_month(self, selected_months=None):
        monthly_data = {}
        for record in self.maintenance_records:
            if selected_months:
                if record.date.strftime('%b').lower() not in [month.lower() for month in selected_months]:
                    continue
            month_key = record.date.strftime('%Y-%m')
            monthly_data[month_key] = monthly_data.get(month_key, 0) + 1

        # Sort by date
        sorted_data = sorted(monthly_data.items(), key=lambda x: x[0])

        # Get last 12 months
        if len(sorted_data) > 12:
            sorted_data = sorted_data[-12:]

        months = [datetime.strptime(date, '%Y-%m').strftime('%b') for date, _ in sorted_data]
        counts = [count for _, count in sorted_data]

        return months, counts

    def get_maintenance_by_type(self, selected_months=None):
        type_counts = {}
        for record in self.maintenance_records:
            if selected_months:
                if record.date.strftime('%b').lower() not in [month.lower() for month in selected_months]:
                    continue
            type_counts[record.maintenance_type] = type_counts.get(record.maintenance_type, 0) + 1

        return type_counts

    def get_resolution_by_type(self, selected_months=None):
        type_resolution = {}
        type_counts = {}

        for record in self.maintenance_records:
            if selected_months:
                if record.date.strftime('%b').lower() not in [month.lower() for month in selected_months]:
                    continue
            if record.maintenance_type not in type_resolution:
                type_resolution[record.maintenance_type] = 0
                type_counts[record.maintenance_type] = 0

            type_resolution[record.maintenance_type] += record.resolution_days
            type_counts[record.maintenance_type] += 1

        avg_resolution = {
            mtype: round(days / type_counts[mtype], 2) if type_counts[mtype] > 0 else 0
            for mtype, days in type_resolution.items()
        }

        return avg_resolution

    def get_performance_by_operator(self, selected_months=None):
        operator_data = {}

        for record in self.maintenance_records:
            if selected_months:
                if record.date.strftime('%b').lower() not in [month.lower() for month in selected_months]:
                    continue
            if record.operator not in operator_data:
                operator_data[record.operator] = {
                    "count": 0,
                    "total_days": 0
                }

            operator_data[record.operator]["count"] += 1
            operator_data[record.operator]["total_days"] += record.resolution_days

        # Calculate average resolution time for each operator
        for operator in operator_data:
            if operator_data[operator]["count"] > 0:
                operator_data[operator]["avg_resolution"] = round(
                    operator_data[operator]["total_days"] / operator_data[operator]["count"], 2
                )
            else:
                operator_data[operator]["avg_resolution"] = 0

        return operator_data

    def get_maintenance_by_day_of_week(self, selected_months=None):
        day_counts = {i: 0 for i in range(7)}  # 0=Monday, 6=Sunday

        for record in self.maintenance_records:
            if selected_months:
                if record.date.strftime('%b').lower() not in [month.lower() for month in selected_months]:
                    continue
            day_of_week = record.date.weekday()
            day_counts[day_of_week] += 1

        days = [calendar.day_name[i][:3] for i in range(7)]
        counts = [day_counts[i] for i in range(7)]

        return days, counts

    def get_maintenance_by_manager(self, selected_months=None):
        manager_counts = {}

        for record in self.maintenance_records:
            if selected_months:
                if record.date.strftime('%b').lower() not in [month.lower() for month in selected_months]:
                    continue
            if record.manager not in manager_counts:
                manager_counts[record.manager] = 0
            manager_counts[record.manager] += 1

        return manager_counts


# ==================== CONTROLLER ====================
class DashboardController:
    def __init__(self, model):
        self.model = model

    def get_dashboard_data(self, selected_months=None):
        data = {
            "total_maintenance": self.model.get_total_maintenance_count(),
            "avg_resolution_time": self.model.get_average_resolution_time(),
            "most_occurrences": self.model.get_equipment_with_most_occurrences(),
            "occurrences_by_month": self.model.get_occurrences_by_month(selected_months),
            "maintenance_by_type": self.model.get_maintenance_by_type(selected_months),
            "resolution_by_type": self.model.get_resolution_by_type(selected_months),
            "performance_by_operator": self.model.get_performance_by_operator(selected_months),
            "maintenance_by_day": self.model.get_maintenance_by_day_of_week(selected_months),
            "maintenance_by_manager": self.model.get_maintenance_by_manager(selected_months)
        }

        return data


# ==================== VIEW ====================
class DashboardView:
    def __init__(self, controller):
        self.controller = controller

    def render_sidebar(self):
        st.sidebar.title("Filtros")
        st.sidebar.subheader("Manutenção e Produção")

        st.sidebar.write("---")
        st.sidebar.write("Gerente")

        managers = ["Danilo", "Marta", "Norma", "Oscar", "Rafael"] # Sample managers from original code
        for manager in sorted(list(set([record['manager'] for record in self.controller.model.get_all_maintenance_records()]))):
            st.sidebar.button(manager) # Dynamically populate from data

        st.sidebar.write("---")
        st.sidebar.write("Tipo de ocorrência")

        occurrence_types = [ # Sample types from original code
            "Engenharia De Manutenção",
            "Manutenção Corretiva Não Planejada",
            "Manutenção Corretiva Planejada",
            "Manutenção Detectiva",
            "Manutenção Preditiva",
            "Manutenção Preventiva"
        ]
        for oc_type in sorted(list(set([record['maintenance_type'] for record in self.controller.model.get_all_maintenance_records()]))):
            st.sidebar.button(oc_type) # Dynamically populate from data

    def render_main_dashboard(self):
        st.title("Controle de Equipamentos")

        # Month selector with reset option
        months_full = calendar.month_name[1:]
        cols = st.columns(len(months_full) + 1)
        selected_months = st.session_state.get('selected_months', [])

        for i, month_name in enumerate(months_full):
            month_abbr = month_name[:3]
            with cols[i]:
                if st.button(month_abbr):
                    if month_name in selected_months:
                        selected_months.remove(month_name)
                    else:
                        selected_months.append(month_name)
                    st.session_state['selected_months'] = selected_months

        with cols[-1]:
            if st.button("Reset Filtros"):
                st.session_state['selected_months'] = []
                selected_months = []

        # Get data from controller based on selected months
        data = self.controller.get_dashboard_data(selected_months)

        # --- Top Metrics ---
        st.write("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de manutenções registradas", f"{data['total_maintenance']:,}")

        with col2:
            st.metric("Tempo médio de resolução (dias)", data['avg_resolution_time'])

        with col3:
            equipment_id, occurrence_count = data['most_occurrences']
            equipment_name = next((eq['name'] for eq in self.controller.model.get_all_equipments() if eq['id'] == equipment_id), "N/A")
            st.metric("Equipamento com mais ocorrências", f"{occurrence_count} - {equipment_name}")

        # --- Monthly Trend Chart ---
        st.write("---")
        st.subheader("Frequência de ocorrências ao longo do tempo")

        months, counts = data['occurrences_by_month']
        if months:
            fig_monthly = px.line(x=months, y=counts, title="Ocorrências mensais", markers=True)
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para os meses selecionados.")

        # --- Maintenance Type Analysis ---
        st.write("---")
        st.subheader("Análise por tipo de manutenção")
        col1, col2 = st.columns(2)

        with col1:
            type_counts = data['maintenance_by_type']
            if type_counts:
                labels = list(type_counts.keys())
                values = list(type_counts.values())
                fig_type = px.pie(names=labels, values=values, title="Distribuição dos tipos de manutenção")
                st.plotly_chart(fig_type, use_container_width=True)
            else:
                st.info("Nenhum dado disponível para os meses selecionados.")

        with col2:
            resolution_by_type = data['resolution_by_type']
            if resolution_by_type:
                types = list(resolution_by_type.keys())
                resolution_times = list(resolution_by_type.values())
                fig_resolution = px.bar(x=types, y=resolution_times, title="Tempo médio de resolução por tipo de manutenção",
                                        labels={'x': 'Tipo de Manutenção', 'y': 'Tempo Médio de Resolução (dias)'})
                st.plotly_chart(fig_resolution, use_container_width=True)
            else:
                st.info("Nenhum dado disponível para os meses selecionados.")

        # --- Operator Performance ---
        st.write("---")
        st.subheader("Performance dos operadores")
        performance_data = data['performance_by_operator']
        if performance_data:
            operators = list(performance_data.keys())
            avg_resolution_times = [perf['avg_resolution'] for perf in performance_data.values()]
            fig_operator = px.bar(x=operators, y=avg_resolution_times,
                                  title="Tempo médio de resolução por operador",
                                  labels={'x': 'Operador', 'y': 'Tempo Médio de Resolução (dias)'})
            st.plotly_chart(fig_operator, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para os meses selecionados.")

        # --- Maintenance by Day of the Week ---
        st.write("---")
        st.subheader("Ocorrências por dia da semana")
        days, day_counts = data['maintenance_by_day']
        if days:
            fig_day = px.bar(x=days, y=day_counts, title="Frequência de ocorrências por dia da semana",
                             labels={'x': 'Dia da Semana', 'y': 'Número de Ocorrências'})
            st.plotly_chart(fig_day, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para os meses selecionados.")

        # --- Maintenance by Manager ---
        st.write("---")
        st.subheader("Ocorrências por gerente")
        manager_counts = data['maintenance_by_manager']
        if manager_counts:
            managers = list(manager_counts.keys())
            counts = list(manager_counts.values())
            fig_manager = px.bar(x=managers, y=counts, title="Número de ocorrências por gerente",
                                 labels={'x': 'Gerente', 'y': 'Número de Ocorrências'})
            st.plotly_chart(fig_manager, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para os meses selecionados.")

        # --- Insights and Analysis ---
        st.write("---")
        st.subheader("Insights e Análise")
        st.info(f"O dashboard apresenta um panorama abrangente da manutenção de equipamentos. Atualmente, há **{data['total_maintenance']:,}** registros de manutenção, com um tempo médio de resolução de **{data['avg_resolution_time']}** dias.")

        if data['most_occurrences'][0]:
            most_frequent_equipment_name = next((eq['name'] for eq in self.controller.model.get_all_equipments() if eq['id'] == data['most_occurrences'][0]), "N/A")
            st.info(f"O equipamento **{most_frequent_equipment_name}** (ID: {data['most_occurrences'][0]}) é o que apresenta a maior frequência de manutenções, com **{data['most_occurrences'][1]}** ocorrências. Isso pode indicar a necessidade de uma análise mais aprofundada sobre a sua condição ou utilização.")

        if months:
            st.info(f"A tendência mensal de ocorrências nos últimos {len(months)} meses mostra uma variação ao longo do tempo. Analisar os picos e vales pode ajudar a identificar padrões sazonais ou eventos específicos que impactam a manutenção.")

        if data['resolution_by_type']:
            most_time_consuming_type = max(data['resolution_by_type'], key=data['resolution_by_type'].get)
            avg_time = data['resolution_by_type'][most_time_consuming_type]
            st.info(f"O tipo de manutenção que demanda o maior tempo médio de resolução é a **{most_time_consuming_type}**, com uma média de **{avg_time}** dias. Focar em otimizar os processos para este tipo de manutenção pode trazer ganhos significativos.")

        if data['performance_by_operator']:
            best_performing_operator = min(data['performance_by_operator'], key=lambda k: data['performance_by_operator'][k]['avg_resolution'])
            best_avg_time = data['performance_by_operator'][best_performing_operator]['avg_resolution']
            st.info(f"O operador com o menor tempo médio de resolução é **{best_performing_operator}**, com uma média de **{best_avg_time}** dias. Identificar as melhores práticas deste operador pode ser valioso para o treinamento de outros.")

        if day_counts:
            most_frequent_day_index = day_counts.index(max(day_counts))
            most_frequent_day = days[most_frequent_day_index]
            st.info(f"A maioria das ocorrências de manutenção tende a acontecer às **{most_frequent_day}**. Isso pode estar relacionado a padrões de uso dos equipamentos ou atividades de planejamento.")

# ==================== MAIN ====================
if __name__ == "__main__":
    model = MaintenanceModel()
    controller = DashboardController(model)
    view = DashboardView(controller)

    view.render_sidebar()
    view.render_main_dashboard()