
from flask import Flask, render_template, request
import requests
import plotly.graph_objs as go
import plotly.io as pio
import datetime
import pandas as pd

app = Flask(__name__)

# Load stock symbols from CSV
def load_stock_symbols():
    df = pd.read_csv('stocks.csv')
    return df['Symbol'].tolist()

def fetch_stock_data(stock_symbol, time_series_function):
    url = f"https://www.alphavantage.co/query?function={time_series_function}&symbol={stock_symbol}&apikey=TKD85DJRC6KNT94C"
    r = requests.get(url)
    return r.json()

def validate_stock_symbol(stock_symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey=TKD85DJRC6KNT94C"
    response = requests.get(url).json()
    if "Error Message" in response or not response.get("Global Quote"):
        return False
    return True

def filter_data_by_date(timeseries, begin_date, end_date):
    filtered_dates = []
    filtered_values_close = []
    filtered_values_open = []
    filtered_values_high = []
    filtered_values_low = []
    for date, value in timeseries.items():
        if begin_date <= date <= end_date:
            filtered_dates.append(date)
            filtered_values_close.append(float(value['4. close']))
            filtered_values_open.append(float(value['1. open']))
            filtered_values_high.append(float(value['2. high']))
            filtered_values_low.append(float(value['3. low']))
    return filtered_dates, filtered_values_close, filtered_values_open, filtered_values_high, filtered_values_low

@app.route('/', methods=['GET', 'POST'])
def index():
    chart = None
    error_message = None
    stock_symbols = load_stock_symbols()

    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol']
        chart_type = request.form['chart_type']
        time_series_function = request.form['time_series_function'].upper()
        begin_date = request.form['begin_date']
        end_date = request.form['end_date']

        if not validate_stock_symbol(stock_symbol):
            error_message = "Invalid stock symbol. Please try a different one."
        elif begin_date >= end_date:
            error_message = "The start date must be before the end date."
        else:
            data = fetch_stock_data(stock_symbol, time_series_function)
            timeseries_key = list(data.keys())[1]
            timeseries = data[timeseries_key]
            filtered_dates, filtered_values_close, filtered_values_open, filtered_values_high, filtered_values_low = filter_data_by_date(timeseries, begin_date, end_date)

            if chart_type == 'line':
                trace_close = go.Scatter(x=filtered_dates, y=filtered_values_close, mode='lines', name='Close')
                trace_open = go.Scatter(x=filtered_dates, y=filtered_values_open, mode='lines', name='Open')
                trace_high = go.Scatter(x=filtered_dates, y=filtered_values_high, mode='lines', name='High')
                trace_low = go.Scatter(x=filtered_dates, y=filtered_values_low, mode='lines', name='Low')
            else:  # Default to bar if anything else is provided
                trace_close = go.Bar(x=filtered_dates, y=filtered_values_close, name='Close')
                trace_open = go.Bar(x=filtered_dates, y=filtered_values_open, name='Open')
                trace_high = go.Bar(x=filtered_dates, y=filtered_values_high, name='High')
                trace_low = go.Bar(x=filtered_dates, y=filtered_values_low, name='Low')

            data = [trace_close, trace_open, trace_high, trace_low]
            layout = go.Layout(title=f'Stock Prices for {stock_symbol} from {begin_date} to {end_date}')
            fig = go.Figure(data=data, layout=layout)

            chart = pio.to_html(fig, full_html=False)

    return render_template('index.html', chart=chart, error_message=error_message, stock_symbols=stock_symbols)

if __name__ == '__main__':
    app.run(debug=True)
