from dash import Dash, html, dcc, callback, Output, Input, State, dash
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd
import os
import io
import base64
import time
import plotly.graph_objects as go
import google.generativeai as genai
import plotly.express as px
from flask import Flask, jsonify, request

server = Flask(__name__)
app = dash.Dash(__name__, server=server, url_base_pathname="/dash/")

df = pd.read_csv(
    "https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/LangChain/Graph-Insights/domain-notable-ai-system.csv"
)


@app.callback(
    Output("interactive-graph", "figure"), [Input("chart-type-dropdown", "value")]
)
def update_graph(selected_chart_type):
    if selected_chart_type == "bar":
        fig = px.bar(
            df, x="Year", y="Annual number of AI systems by domain", color="Entity"
        )
    elif selected_chart_type == "line":
        fig = px.line(
            df, x="Year", y="Annual number of AI systems by domain", color="Entity"
        )
    else:
        fig = px.scatter(
            df, x="Year", y="Annual number of AI systems by domain", color="Entity"
        )
    return fig


@server.route("/update_graph", methods=["POST"])
def update_graph_data():
    data = request.json
    chart_type = data["chartType"]
    fig = update_graph(chart_type)
    fig_json = fig.to_json()
    insights = "Generated insights based on the selected chart type."  # Placeholder for actual insights
    return jsonify({"figure": fig_json, "insights": insights})


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
