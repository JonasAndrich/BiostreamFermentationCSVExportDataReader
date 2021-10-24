# -----------------------------------------------------------
# Visualization of fermentation data in a Dash-Web-App
# Reads the CSV-Files specificly exported by the Biostream BOS-Software
# CSV-Files exported with ";" as separation symbol, "," as decimal symbol and "ISO-8859-1"-encoding.
# (C) 2021 Jonas Andrich, Hamburg, Germany
# Released under GNU Public License (GPL)
# email Jonas.Andrich@gmail.com
# -----------------------------------------------------------

# Dash-Compounds
# from jupyter_dash import JupyterDash
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# Pandas
import pandas as pd

# Plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# System
import base64
import io

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

server = app.server

app.layout = html.Div([
    html.H1("Biostream Fermentation Data Reader"),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
    ),

    html.Div(id='figure-input'),
    html.Div(id='FermentationDataGraph'),
])


@app.callback(Output('figure-input', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              prevent_initial_call=True)
def update_output(contents, name, date):
    if contents is not None:
        df = parse_contents(contents)
        children = html.Div([
            html.H2(name),
            html.Label([('Primary Y-Axis'),
                        dcc.Dropdown(
                            id='Y-Value1',
                            options=[
                                {'label': c, 'value': c}
                                for c in (df.columns.values)
                            ],
                            value=["pO2 Value (%)",
                                   'Temperature Value (°C)',
                                   'Flow - Air Value (L/m)',
                                   'pH Value (pH)',
                                   ],
                            multi=True
                        ),

                        ]),

            html.Label([('Select Secondary Y-Axis'),
                        dcc.Dropdown(
                            id='Y-Value2',
                            options=[
                                {'label': c, 'value': c}
                                for c in (df.columns.values)
                            ],

                            value=['BlueInOne - CO2 Value (%)',
                                   'BlueInOne - O2 Value (%)'],
                            multi=True
                        ),
                        ]),

            html.Label([('Select X'),
                        dcc.RadioItems(
                            id='X-Value',
                            options=[

                                {'label': 'timestamp', 'value': 'timestamp'},
                                {'label': 'time [h]', 'value': 'time [h]'},
                            ],

                            value='time [h]'
                        ),
                        ]),

        ])

        return children


# callback to update graph
@app.callback(
    Output('FermentationDataGraph', 'children'),
    Input('Y-Value1', 'value'),
    Input('Y-Value2', 'value'),
    Input('X-Value', 'value'),
    State('upload-data', 'contents'),
    prevent_initial_call=True
)
def update_figure(YValue1, YValue2, XValue, contents):
    if contents is not None:
        df = parse_contents(contents)

    # Groups of Parameter ranges
    # ph 1-7
    # Exit CO2 0,2 - 6
    # L/min 0-2
    # RQ 0 - 5
    # Exit O2 12-20
    # Temperature 20- 37
    # O2 0-100
    # Waage 0-1000 g
    # Stirrer 600-1200

    # Set x-axis data and title based on selection
    X = df[XValue].tolist()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(xaxis_title=XValue)

    # List for Titles of the Y-Axis elements
    primary_title_list = []
    secondary_title_list = []

    for element in YValue1:
        Y = df[element].tolist()
        fig.add_trace(go.Scatter(x=X, y=Y, name=element), secondary_y=False)
        primary_title_list.append(element)

    for element in YValue2:
        Y = df[element].tolist()
        fig.add_trace(go.Scatter(x=X, y=Y, name=element), secondary_y=True)
        secondary_title_list.append(element)

    # Merge and set primary y-axes titles
    fig.update_yaxes(
        title_text='<br> '.join(primary_title_list),
        secondary_y=False)

    # Merge and set secondary y-axes titles
    fig.update_yaxes(
        title_text='<br> '.join(secondary_title_list),
        secondary_y=True)

    # Formatieren der Graphen-Legende
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))

    # Größe des Graphen und Zeit Dauer Veränderung wenn Werte geändert werden
    fig.update_layout(
        transition_duration=500,
        autosize=True,
        # width=500,
        # height=700,
    )

    children = dcc.Graph(
        figure=fig
    )
    return children


def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        data = pd.read_csv(
            io.StringIO(decoded.decode("ANSI")),
            sep=";",
            decimal=",",
            encoding="utf-8")

        # print(list(data.columns.values))

        # Anpassen der Daten für den Biostream
        data['timestamp'] = pd.to_datetime(data['Date'] + ' ' + data['Time'], format="%d.%m.%Y %H:%M:%S")
        data["time [s]"] = pd.to_timedelta(data['timestamp'] - data['timestamp'][0])
        data["time [s]"] = data["time [s]"].dt.total_seconds()
        data['time [h]'] = data["time [s]"] / 3600
        df = data.rename(columns={'pO? Value': "pO2 Value (%)"})

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df


if __name__ == '__main__':
    app.run_server(debug=True)