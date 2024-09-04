from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import requests

app = Flask(__name__)

def fetch_covid_data():
    url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    response = requests.get(url)
    with open('time_series_covid19_confirmed_global.csv', 'wb') as file:
        file.write(response.content)

    df = pd.read_csv('time_series_covid19_confirmed_global.csv')
    return df

def get_country_list():
    df = fetch_covid_data()
    return df['Country/Region'].unique()

def get_country_data(country):
    df = fetch_covid_data()
    country = country.strip()
    available_countries = df['Country/Region'].unique()

    country_match = next((c for c in available_countries if country.lower() in c.lower()), None)
    if not country_match:
        print(f'Country not found: {country}')
        return pd.DataFrame()

    df_country = df[df['Country/Region'] == country_match]
    df_country = df_country.melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], var_name='Date',
                                 value_name='Cases')
    df_country['Date'] = pd.to_datetime(df_country['Date'])
    return df_country

@app.route('/', methods=['GET'])
def index():
    chart_type = request.args.get('chart_type', 'line')
    country = request.args.get('country', 'Brazil')

    df = get_country_data(country)
    if df.empty:
        return f'No data found for {country}', 404

    df_long = df.melt(id_vars=['Date'], var_name='Metric', value_name='Value')

    if chart_type == 'line':
        fig = px.line(df_long, x='Date', y='Value', color='Metric', title=f'Casos Confirmados em {country}')
    elif chart_type == 'bar':
        fig = px.bar(df_long, x='Date', y='Value', color='Metric', title=f'Casos Confirmados em {country}')
    elif chart_type == 'area':
        fig = px.area(df_long, x='Date', y='Value', color='Metric', title=f'Casos Confirmados em {country}')
    elif chart_type == 'box':
        fig = px.box(df_long, x='Date', y='Value', color='Metric', title=f'Box Plot de Casos Confirmados em {country}')
    elif chart_type == 'scatter':
        fig = px.scatter(df_long, x='Date', y='Value', color='Metric', title=f'Casos Confirmados em {country}')
    elif chart_type == 'heatmap':
        df_heatmap = df_long.pivot_table(index='Date', columns='Metric', values='Value', aggfunc='sum').fillna(0)
        fig = px.imshow(df_heatmap, title=f'Mapa de Calor de Casos Confirmados em {country}')
    elif chart_type == 'histogram':
        fig = px.histogram(df_long, x='Value', title=f'Histograma de Casos Confirmados em {country}')

    graph_html = fig.to_html(full_html=False)

    return render_template('index.html', graph_html=graph_html, selected_country=country, selected_chart_type=chart_type)


    return render_template('index.html', graph_html=graph_html)

@app.route('/countries', methods=['GET'])
def countries():
    country_list = get_country_list()
    filtered_countries = [c for c in country_list if 'USA' not in c and 'United States' not in c]
    return jsonify({'countries': filtered_countries})

@app.route('/debug', methods=['GET'])
def debug():
    df = fetch_covid_data()
    country_list = df['Country/Region'].unique()
    return jsonify({'available_countries': country_list.tolist()})

if __name__ == '__main__':
    app.run(debug=True)
