from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage


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

# from dotenv import find_dotenv, load_dotenv
import google.generativeai as genai


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
                dcc.Store(id="stored-fileName", dat=fileName),
                html.Hr(),
            ]
        )

    def page(self):
        layout = [
            html.H1("IA Criando graficos"),
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
                id="output-text",
                placeholder="Output will be here...",
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

        return layout

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
    def create_grafico(self, user_input, file_data, fileName):

        df = pd.DataFrame(file_data)
        df_sample = df.head()
        csv_string = df_sample.to_string(index=False)

        self.genAI.generativeAI(
            "Voce é uma visualizador de dados e voce so usa Plotty, analise os dados e gere graficos"
        )
