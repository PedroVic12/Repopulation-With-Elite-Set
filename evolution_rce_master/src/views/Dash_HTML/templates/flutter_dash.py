import dash

import dash_material_components as dmc


# Compose a dashboard layout
text = dmc.Typography(text="Content...", component="p", variant="body2")
text_2 = dmc.Typography(text="OLA MUNDO...", component="p", variant="body2")


section_1 = dmc.Section(
    id="section-1",
    orientation="columns",
    children=[text, text_2],
    cards=[{"title": "Card 1a", "size": 3}, {"title": "Card 1b"}],
)

section_2 = dmc.Section(
    id="section-2",
    size=3,
    children=[text, text_2],
    orientation="rows",
    cards=[{"title": "Card 2a", "size": 4}, {"title": "Card 2b"}],
)

page = dmc.Page(orientation="columns", children=[section_1, section_2])


navbar = dmc.NavBar(title="Custom dash")

layout = dmc.Dashboard(children=[navbar, page])

# Instantiate a Dash app
app = dash.Dash(__name__)
app.layout = layout

if __name__ == "__main__":
    app.run_server(
        debug=True,
        port=8051,
    )
