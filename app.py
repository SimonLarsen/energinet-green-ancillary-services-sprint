import dash
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html
from datetime import date
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from get_mean_per_prodtype import get_prod_proportion
from get_co2_equiv import get_co2_reduction


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
                dbc.Input(id="up-available", placeholder="Tilgængelige", type="number", min=0, step=0.1),
                dbc.InputGroupText("MW")
            ], className="mb-1"),
            dbc.InputGroup([
                dbc.Input(id="up-activated", placeholder="Aktiveret", type="number", min=0, max=100, step=0.1),
                dbc.InputGroupText("%")
            ])
        ], md=6, lg=3),
        dbc.Col([
            html.H3("Nedregulering", className="display-6"),
            dbc.InputGroup([
                dbc.Input(id="down-available", placeholder="Tilgængelige", type="number", min=0, step=0.1),
                dbc.InputGroupText("MW")
            ], className="mb-1"),
            dbc.InputGroup([
                dbc.Input(id="down-activated", placeholder="Aktiveret", type="number", min=0, max=100, step=0.1),
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
            html.H1([html.Img(src=app.get_asset_url("Balance.png"), style={"width": "80px", "margin-right": "10px"}), "FlexFordel"], className="display-4"),
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
    if date_start is None or date_end is None or area is None:
        return EMPTY_GRAPH

    df = get_prod_proportion(
        "data/declarationcoveragehour.parquet",
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
    State("date-period", "end_date"),
    State("dropdown-area", "value"),
    State("up-available", "value"),
    State("up-activated", "value"),
    State("down-available", "value"),
    State("down-activated", "value")
)
def update_graph_reduction(n_clicks, date_start, date_end, area, up_available, up_activated, down_available, down_activated):
    if date_start is None or date_end is None or area is None:
        return EMPTY_GRAPH
    
    up_available = up_available or 0
    up_activated = up_activated or 0
    down_available = down_available or 0
    down_activated = down_activated or 0

    date_start = pd.Timestamp(date_start, tz="UTC")
    date_end = pd.Timestamp(date_end, tz="UTC")
    dates = pd.date_range(date_start, date_end+pd.offsets.Day(), freq="D", closed="left")

    data = get_co2_reduction(date_start, date_end, area)
    data = data.resample("D").mean()

    total_up = up_available * 1000 * up_activated / 100 * 24
    total_down = down_available * 1000 * down_activated / 100 * 24

    reduced_up = data["CO2Diff"] * total_up / 1000
    reduced_down = data["CO2Equiv"] * total_down / 1000

    fig = go.Figure(data=[
        go.Bar(name="Op", x=data.index, y=reduced_up),
        go.Bar(name="Ned", x=data.index, y=reduced_down)
    ])
    fig.update_layout(
        barmode="stack",
        height=GRAPH_HEIGHT,
        title={"text": "Din besparelse"},
        yaxis_title="Kg CO2 pr. dag"
    )
    return fig


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=4000, debug=False)
