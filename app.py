import pkgutil, importlib.util
if not hasattr(pkgutil, "find_loader"):
    def find_loader(name):
        spec = importlib.util.find_spec(name)
        return spec
    pkgutil.find_loader = find_loader

import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

# LOAD DATASET (EXCEL)
df = pd.read_excel("C:/Analitik dan visualisasi data/Dashboard TB/Dataset.xlsx")

# Normalisasi kolom
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace(".", "", regex=False)
)

# Deteksi kolom penting
kolom_negara = [c for c in df.columns if "country" in c or "negara" in c][0]
kolom_pm25   = [c for c in df.columns if "pm25" in c or "pm_25" in c][0]
kolom_pm10   = [c for c in df.columns if "pm10" in c or "pm_10" in c][0]
kolom_tahun  = [c for c in df.columns if "year" in c or "tahun" in c][0]

kolom_lat = next((c for c in df.columns if "lat" in c), None)
kolom_lon = next((c for c in df.columns if "lon" in c), None)

# DASH APP
app = Dash(__name__)
app.title = "Dashboard Kualitas Udara PM2.5 & PM10"

# LAYOUT
app.layout = html.Div([

    html.H1("Dashboard Kualitas Udara Global", style={"textAlign": "center"}),

    html.Div([
        html.Div([
            html.Label("Pilih Negara"),
            dcc.Dropdown(
                id="dropdown-negara",
                options=[{"label": n, "value": n} for n in df[kolom_negara].unique()],
                value=df[kolom_negara].unique()[0],
            ),
        ], style={"width": "30%", "display": "inline-block"}),

        html.Div([
            html.Label("Pilih Indikator"),
            dcc.RadioItems(
                id="pilihan-indikator",
                options=[
                    {"label": "PM2.5", "value": kolom_pm25},
                    {"label": "PM10", "value": kolom_pm10},
                ],
                value=kolom_pm25,
                inline=True
            ),
        ], style={"width": "30%", "display": "inline-block"}),

        html.Div([
            html.Label("Filter Tahun"),
            dcc.Slider(
                id="slider-tahun",
                min=df[kolom_tahun].min(),
                max=df[kolom_tahun].max(),
                step=1,
                value=df[kolom_tahun].min(),
                marks={int(y): str(int(y)) for y in df[kolom_tahun].unique()}
            ),
        ], style={"width": "40%", "display": "inline-block", "padding": "0px 20px"}),
    ]),

    html.Br(),

    dcc.Graph(id="bar-top10"),
    dcc.Graph(id="line-trend"),
    dcc.Graph(id="scatter"),
    dcc.Graph(id="geo-map")

])

# CALLBACK
@app.callback(
    [
        Output("bar-top10", "figure"),
        Output("line-trend", "figure"),
        Output("scatter", "figure"),
        Output("geo-map", "figure")
    ],
    [
        Input("dropdown-negara", "value"),
        Input("pilihan-indikator", "value"),
        Input("slider-tahun", "value")
    ]
)
def update_dashboard(selected_country, indikator, tahun_pilih):

    # Filter berdasarkan tahun
    df_filtered = df[df[kolom_tahun] == tahun_pilih]

    # Bar Top 10
    top10 = df_filtered.groupby(kolom_negara)[indikator].mean().nlargest(10).reset_index()
    fig_bar = px.bar(
        top10, 
        x=kolom_negara, 
        y=indikator,
        title=f"Top 10 Negara dengan {indikator.upper()} pada Tahun {tahun_pilih}",
        color=indikator,
        color_continuous_scale="Oranges"
    )

    # Line Trend
    trend = df.groupby(kolom_tahun)[indikator].mean().reset_index()
    fig_line = px.line(
        trend, 
        x=kolom_tahun, 
        y=indikator,
        title=f"Tren {indikator.upper()} Tahunan Global",
        markers=True
    )

    # Scatter
    fig_scatter = px.scatter(
        df_filtered, 
        x=kolom_pm10, 
        y=kolom_pm25,
        color=kolom_negara,
        opacity=0.6,
        trendline="ols",
        title=f"Hubungan PM10 vs PM2.5 (Tahun {tahun_pilih})"
    )

    # Geo Map
    if kolom_lat and kolom_lon:
        fig_geo = px.scatter_geo(
            df_filtered,
            lat=kolom_lat, lon=kolom_lon,
            color=indikator,
            hover_name=kolom_negara,
            title=f"Sebaran Spasial {indikator.upper()} (Tahun {tahun_pilih})",
            color_continuous_scale="Reds",
            projection="natural earth"
        )
    else:
        avg_country = df_filtered.groupby(kolom_negara)[indikator].mean().reset_index()
        fig_geo = px.choropleth(
            avg_country,
            locations=kolom_negara,
            locationmode="country name",
            color=indikator,
            title=f"Peta {indikator.upper()} per Negara (Tahun {tahun_pilih})",
            color_continuous_scale="Reds"
        )

    return fig_bar, fig_line, fig_scatter, fig_geo


# RUN APP
if __name__ == "__main__":
    app.run(
        debug=False,
        dev_tools_ui=False,
        dev_tools_props_check=False,
        dev_tools_silence_routes_logging=True
    )
