from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd
import re
import os
import io
import base64
import time
import plotly.graph_objects as go
import google.generativeai as genai
import plotly.express as px

# from dotenv import find_dotenv, load_dotenv

# dotenv_path = find_dotenv()
# load_dotenv(dotenv_path)  # load api key


class genaiInterpretador:

    def __init__(self):
        genai.configure(api_key=os.getenv("AIzaSyCZhKI6vWIAK0GkzXajc-PUjTBEO5zjoeA"))

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_chart(self, fig):
        fig_object = go.Figure(fig)
        fig_object.write_image(f"images/fig.png")
        time.sleep(1)

        image_path = f"images/fig.png"
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = genai.generate_text(
            model="gemini-pro",
            prompt=f"Descreva os insights do gráfico: \n\n"
            f"O gráfico é: {base64_image}",
            temperature=0.7,
        )

        return response.text

    def generativeAI(self, prompt):
        response = genai.generate_text(
            model="gemini-pro",
            prompt=prompt,
            temperature=0.7,
        )
        return response.text


class DashIA:
    def __init__(self):
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )

        self.genAI = genaiInterpretador()

    def get_fig_from_code(self, code):
        local_variables = {}
        exec(code, {}, local_variables)
        return local_variables["fig"]

    def parse_contents(self, contents, fileName):
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        try:
            if "csv" in fileName:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

            elif "xls" in fileName:
                # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))

        except Exception as error:
            print(error)
            return html.Div(["There was an error processing this file."])

        return html.Div(
            [
                html.H5(fileName),
                dag.AgGrid(
                    rowData=df.to_dict("records"),
                    columnDefs=[{"field": i} for i in df.columns],
                    defaultColDef={
                        "filter": True,
                        "sortable": True,
                        "flex": 1,
                        "editable": True,
                        "floatingFilter": True,
                    },
                ),
                dcc.Store(
                    id="stored-data",
                    data=df.to_dict("records"),
                ),
                dcc.Store(id="stored-fileName", data=fileName),
                html.Hr(),
            ]
        )

    def page(self):
        layout = [
            html.H1("IA Criando Graficos"),
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        "Drag and Drop or ",
                        html.A("Select Files"),
                    ]
                ),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                multiple=True,
            ),
            html.Div(id="output-grid"),
            dcc.Textarea(
                id="user-request",
                placeholder="Digite o tipo de gráfico que você deseja (ex: gráfico de barras, gráfico de linhas)",
                style={
                    "width": "100%",
                    "height": 50,
                },
            ),
            html.Br(),
            html.Button("Submit", id="my-button"),
            dcc.Loading(
                [
                    html.Div(id="my-figure", children=""),
                    dcc.Markdown(id="conteudo", children=""),
                ],
                type="cube",
            ),
        ]

        return dbc.Container(layout)  # Retorna o layout como um único componente

    @callback(
        Output("output-grid", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
    )
    def update_output(self, list_of_contents, list_of_names):
        if list_of_contents is not None:
            children = [
                self.parse_contents(c, n)
                for c, n in zip(list_of_contents, list_of_names)
            ]
            return children

    @callback(
        Output("my-figure", "children"),
        Output("conteudo", "children"),
        Input("my-button", "n_clicks"),
        State("user-request", "value"),
        State("stored-data", "data"),
        State("stored-fileName", "data"),
    )
    def create_grafico(self, user_input, user_request, file_data, fileName):
        if user_input is None:
            return "", ""

        df = pd.DataFrame(file_data)
        df_sample = df.head()
        csv_string = df_sample.to_string(index=False)

        # Incorporate the data
        df = pd.read_csv(
            "https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/LangChain/Graph-Insights/domain-notable-ai-system.csv"
        )

        if user_request == "gráfico de barras":
            fig = px.bar(
                df, x="Year", y="Annual number of AI systems by domain", color="Entity"
            )
        elif user_request == "gráfico de linhas":
            fig = px.line(
                df, x="Year", y="Annual number of AI systems by domain", color="Entity"
            )
        else:
            fig = px.scatter(
                df, x="Year", y="Annual number of AI systems by domain", color="Entity"
            )

        fig.update_layout(legend_title=None)
        fig_json = fig.to_json()
        graph_div = dcc.Graph(figure=fig)

        # Generative AI Insights
        if user_request is not None and user_request != "":
            insights = self.genAI.generativeAI(
                f"Voce é um visualizador de dados e voce so usa Plotty, crie um {user_request} com os dados em  '{csv_string}'  e me descreva os insights que você pode ver no gráfico."
            )
        else:
            insights = self.genAI.generativeAI(
                f"Voce é um visualizador de dados e voce so usa Plotty, crie um gráfico com os dados em  '{csv_string}'  e me descreva os insights que você pode ver no gráfico."
            )

        return graph_div, insights


if __name__ == "__main__":
    app = DashIA()
    app.app.layout = app.page()
    app.app.run_server(debug=True)
