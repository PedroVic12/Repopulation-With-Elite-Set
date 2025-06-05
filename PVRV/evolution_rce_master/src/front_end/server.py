import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px


# Criando a classe do backend
class Backend:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.df = pd.read_csv(
            "https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/LangChain/Graph-Insights/domain-notable-ai-system.csv"
        )
        self.chart_types = ["Bar Chart", "Line Chart", "Scatter Chart"]

        self.app.layout = html.Div(
            children=[
                html.H1(children="Interactive Data Visualization"),
                dcc.Dropdown(
                    id="chart-type",
                    options=[{"label": i, "value": i} for i in self.chart_types],
                    value="Bar Chart",
                ),
                dcc.Graph(id="interactive-graph"),
                html.Div(id="insights"),
                dag.AgGrid(
                    id="data-table",
                    columnDefs=[
                        {"headerName": "Year", "field": "Year"},
                        {
                            "headerName": "Annual number of AI systems by domain",
                            "field": "Annual number of AI systems by domain",
                        },
                        {"headerName": "Entity", "field": "Entity"},
                    ],
                    rowData=self.df.to_dict("records"),
                    dashGridOptions={"pagination": True, "paginationPageSize": 10},
                ),
            ]
        )

        # Callback para atualizar o gráfico e os insights
        @self.app.callback(
            [
                dash.Output("interactive-graph", "figure"),
                dash.Output("insights", "children"),
            ],
            [dash.Input("chart-type", "value")],
        )
        def update_graph(selected_chart):
            fig = self.create_chart(selected_chart)
            insights = self.generate_insights(selected_chart)
            return fig, insights

        # Iniciar o servidor Dash
        self.app.run_server(debug=True)

    def create_chart(self, selected_chart):
        fig = None
        if selected_chart == "Bar Chart":
            fig = px.bar(
                self.df,
                x="Year",
                y="Annual number of AI systems by domain",
                color="Entity",
            )
        elif selected_chart == "Line Chart":
            fig = px.line(
                self.df,
                x="Year",
                y="Annual number of AI systems by domain",
                color="Entity",
            )
        elif selected_chart == "Scatter Chart":
            fig = px.scatter(
                self.df,
                x="Year",
                y="Annual number of AI systems by domain",
                color="Entity",
            )

        fig.update_layout(
            title=f"{selected_chart} of AI Systems by Domain",
            xaxis_title="Year",
            yaxis_title="Annual Number of AI Systems",
            legend_title="Entity",
        )
        return fig

    def generate_insights(self, selected_chart):
        # Aqui você pode implementar lógica para gerar insights
        # baseados no tipo de gráfico selecionado.
        return f"This {selected_chart} shows the trends in the number of AI systems across different domains over time. You can see that..."


# Iniciar o backend
backend = Backend()
backend.app.run_server(debug=True)
