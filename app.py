import dash
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html
from datetime import date
import plotly.express as px
import pandas as pd
import numpy as np
from get_mean_per_prodtype import get_prod_proportion


VALID_YEARS = [2017, 2018, 2019, 2020]
VALID_MONTHS = ["Januar", "Februar", "Marts", "April", "Maj", "Juni", "Juli", "August", "September", "Oktober", "November", "December"]
EMPTY_GRAPH = {
    "layout": {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "height": 48
    }
}
GRAPH_HEIGHT = 500


app = dash.Dash(external_stylesheets=[dbc.themes.LUMEN])

form_content = html.Div([
    dbc.Row([
        dbc.Col([
            html.H3("Prisområde", className="display-6"),
            dcc.Dropdown(
                id="dropdown-area",
                options=[
                    {"label": "DK1", "value": "DK1"},
                    {"label": "DK2", "value": "DK2"}
                ],
                clearable=False
            )
        ], md=6, lg=3),
        dbc.Col([
            html.H3("Periode", className="display-6"),
            dcc.DatePickerRange(
                id="date-period",
                min_date_allowed=date(2017, 1, 1),
                max_date_allowed=date(2020, 12, 31),
                initial_visible_month=date(2020, 6, 1),
                updatemode="bothdates",
                minimum_nights=7
            )
        ], md=6, lg=3),
        dbc.Col([
            html.H3("Opregulering", className="display-6"),
            dbc.InputGroup([
                dbc.Input(placeholder="Tilgængelige", type="number", min=0, step=0.1),
                dbc.InputGroupText("MW")
            ], className="mb-1"),
            dbc.InputGroup([
                dbc.Input(placeholder="Aktiveret", type="number", min=0, max=100, step=0.1),
                dbc.InputGroupText("%")
            ])
        ], md=6, lg=3),
        dbc.Col([
            html.H3("Nedregulering", className="display-6"),
            dbc.InputGroup([
                dbc.Input(placeholder="Tilgængelige", type="number", min=0, step=0.1),
                dbc.InputGroupText("MW")
            ], className="mb-1"),
            dbc.InputGroup([
                dbc.Input(placeholder="Aktiveret", type="number", min=0, max=100, step=0.1),
                dbc.InputGroupText("%")
            ])
        ], md=6, lg=3)
    ])
])

results_content = html.Div(
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id="graph-pie")), lg=5),
        dbc.Col(dcc.Loading(dcc.Graph(id="graph-reduction")), lg=7)
    ])
)

app.layout = dbc.Container(
    [
        html.Div([
            html.H1("FlexFordel", className="display-4"),
            html.P("Beregn dit bidrag til den grønne omstilling.", className="lead"),
        ], className="my-4 text-center"),
        form_content,
        html.Div(
            dbc.Button("Beregn", id="button-submit", color="primary", size="lg"),
            className="my-4 d-flex justify-content-center"
        ),
        results_content,
        html.Footer(
            html.P("Energinet | Grønne Systemydelser | FlexFordel prototype", className="text-muted my-3"),
            className="border-top"
        )
    ],
    className="p-3"
)


@app.callback(
    Output("graph-pie", "figure"),
    Input("button-submit", "n_clicks"),
    State("date-period", "start_date"),
    State("date-period", "end_date"),
    State("dropdown-area", "value")
)
def update_graph_pie(n_clicks, date_start, date_end, area):
    if date_start is None or date_end is None:
        return EMPTY_GRAPH

    df = get_prod_proportion(
        "declarationcoveragehour.parquet",
        date_start,
        date_end,
        area
    )
    fig = px.pie(
        df,
        values="Share",
        names="ProductionGroup",
        title="Du erstatter",
        labels={
            "ProductionGroup": "Produktionstype",
            "Share": "Andel"
        },
        height=GRAPH_HEIGHT
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update(layout_showlegend=False)
    return fig


@app.callback(
    Output("graph-reduction", "figure"),
    Input("button-submit", "n_clicks"),
    State("date-period", "start_date"),
    State("date-period", "end_date")
)
def update_graph_reduction(n_clicks, date_start, date_end):
    if date_start is None or date_end is None:
        return EMPTY_GRAPH

    date_start = pd.Timestamp(date_start, tz="UTC")
    date_end = pd.Timestamp(date_end, tz="UTC")
    dates = pd.date_range(date_start, date_end+pd.offsets.Day(), freq="D", closed="left")

    return px.bar(
        x=dates,
        y=np.random.randint(10, 50, len(dates)),
        title="Estimeret besparelse",
        labels={
            "x": "Dag",
            "y": "Gram CO2"
        },
        height=GRAPH_HEIGHT
    )


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=4000, debug=True)
