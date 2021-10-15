import argparse
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
GRAPH_HEIGHT = 400
EMPTY_GRAPH = {
    "layout": {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "height": GRAPH_HEIGHT
    }
}

PROD_TYPES = ["Kul", "Naturgas", "Atomkraft", "Olie", "Biomasse", "Affald", "Biogas"]
ENERGINET_COLORS = ["#00A58D", "#09505D", "#FFD424", "#83CCD8", "#008A8B", "#F8AE3C", "#A0C1C2", "#9FCD91", "#CC493E"]
PRIMARY_COLOR = ENERGINET_COLORS[0]
PROD_COLOR_MAP = {t: c for t, c in zip(PROD_TYPES, ENERGINET_COLORS[1:8])}

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LUMEN],
    title="FlexFordel"
)

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
            html.H3("Type", className="display-6"),
            dcc.Dropdown(
                id="dropdown-type",
                options=[
                    {"label": "Opregulering", "value": "up"},
                    {"label": "Nedregulering", "value": "down"}
                ],
                clearable=False
            )
        ], md=6, lg=3),
        dbc.Col([
            html.H3("Produkt", className="display-6"),
            dbc.InputGroup([
                dbc.Input(id="input-available", placeholder="Tilgængelige", type="number", min=0, step=0.01),
                dbc.InputGroupText("MW")
            ], className="mb-1"),
            dbc.InputGroup([
                dbc.Input(id="input-activated", placeholder="Aktiveret", type="number", min=0, max=100, step=0.01),
                dbc.InputGroupText("%")
            ])
        ], md=6, lg=3)
    ])
])


def kpi_card(id, title, value, unit):
    return dbc.Card([
        dbc.CardHeader(html.H4(title, className="m-0 card-title")),
        dbc.CardBody([
            html.Span(value, id=id, className="h1"),
            html.Span(unit, className="ml-1 h3 fw-light text-muted")
        ])
    ], color="success", outline=True)


results_content = dbc.Collapse(dcc.Loading([
    html.Hr(),
    dbc.Row([
        dbc.Col(kpi_card("kpi-total", "Samlet besparelse", "--", "kg CO2"), md=6, lg=3),
        dbc.Col(kpi_card("kpi-mean", "Gennemsnit", "--", "g CO2/kWh"), md=6, lg=3)
    ], className="justify-content-lg-center text-center mb-3"),
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(id="graph-pie"), className="border p-2 rounded"), lg=5),
        dbc.Col(html.Div(dcc.Graph(id="graph-reduction"), className="border p-2 rounded"), lg=7)
    ])
]), id="collapse-results", is_open=False)


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
            className="mt-3 border-top"
        )
    ],
    className="p-2"
)


@app.callback(
    Output("collapse-results", "is_open"),
    Input("button-submit", "n_clicks"),
    State("date-period", "start_date"),
    State("date-period", "end_date"),
    State("dropdown-area", "value"),
    State("dropdown-type", "value")
)
def update_graph_pie(n_clicks, date_start, date_end, area, product_type):
    if date_start is None or date_end is None or area is None or product_type is None:
        return False
    else:
        return True


@app.callback(
    Output("graph-pie", "figure"),
    Input("button-submit", "n_clicks"),
    State("date-period", "start_date"),
    State("date-period", "end_date"),
    State("dropdown-area", "value"),
    State("dropdown-type", "value")
)
def update_graph_pie(n_clicks, date_start, date_end, area, product_type):
    if date_start is None or date_end is None or area is None or product_type is None:
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
        color="ProductionGroup",
        title="Du erstatter",
        labels={
            "ProductionGroup": "Produktionstype",
            "Share": "Andel"
        },
        color_discrete_map=PROD_COLOR_MAP,
        height=GRAPH_HEIGHT
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        showlegend=False,
        margin=dict(t=40, r=20, b=24, l=20)
    )
    return fig


@app.callback(
    Output("graph-reduction", "figure"),
    Output("kpi-total", "children"),
    Output("kpi-mean", "children"),
    Input("button-submit", "n_clicks"),
    State("date-period", "start_date"),
    State("date-period", "end_date"),
    State("dropdown-area", "value"),
    State("dropdown-type", "value"),
    State("input-available", "value"),
    State("input-activated", "value")
)
def update_graph_reduction(n_clicks, date_start, date_end, area, product_type, available, activated):
    if date_start is None or date_end is None or area is None or product_type is None:
        return EMPTY_GRAPH, "--", "--"

    available = available or 0
    activated = activated or 0

    date_start = pd.Timestamp(date_start, tz="UTC")
    date_end = pd.Timestamp(date_end, tz="UTC")
    dates = pd.date_range(date_start, date_end+pd.offsets.Day(), freq="D", closed="left")

    data = get_co2_reduction(date_start, date_end, area)
    data = data.resample("D").mean()

    co2_ref = data["CO2Diff"] if product_type == "up" else data["CO2Equiv"]
    total = available * 1000 * activated / 100 * 24
    reduced = co2_ref * total / 1000

    fig = px.bar(
        x=data.index,
        y=reduced,
        title="Din besparelse",
        labels={
            "y": "Kg CO2 pr. dag"
        },
        height=GRAPH_HEIGHT
    )
    fig.update_traces(marker_color=PRIMARY_COLOR)
    fig.update_layout(
        showlegend=False,
        margin=dict(t=40, r=10, b=10, l=10)
    )
    fig.update_xaxes(title_text="")

    kpi_total = "{:d}".format(round(reduced.sum()))
    kpi_mean = "{:d}".format(round(co2_ref.mean()))
    return fig, kpi_total, kpi_mean


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=4000)
    args = parser.parse_args()

    app.run_server(host="0.0.0.0", port=args.port, debug=False)
