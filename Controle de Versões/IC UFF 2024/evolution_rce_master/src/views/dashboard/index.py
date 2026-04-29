from dash import html, dcc
import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# from app import app
from app import *
from pages import sidebar, page1, page2, plots_rce

# =========  Layout  =========== #
content = html.Div(id="page-content")

app.layout = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Location(id="url"),
                        sidebar.layout,
                    ],
                    md=2,
                ),
                dbc.Col([content], md=10),
            ]
        )
    ],
    style={"padding": "0px"},
)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return page1.layout

    elif pathname == "/pages":
        return page2.layout

    elif pathname == "/dash":
        return plots_rce.layout

    # elif pathname == "/dash":
    #    return simple_dash.layout


if __name__ == "__main__":
    app.run_server(port=8090, host="0.0.0.0")
