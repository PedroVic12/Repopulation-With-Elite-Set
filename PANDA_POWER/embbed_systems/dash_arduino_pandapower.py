import serial
import sqlite3
import pandapower as pp
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime
import pandas as pd

query_sql1 = """
CREATE TABLE arduino_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    led1 INTEGER,
    led2 INTEGER,
    led3 INTEGER,
    voltage REAL
);

CREATE TABLE pandapower_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    bus_voltage REAL,
    active_power REAL,
    reactive_power REAL
);


"""

# Configuração do Arduino
arduino = serial.Serial('/dev/ttyUSB0', 9600)  # Ajuste a porta conforme necessário

# Configuração do banco de dados
conn = sqlite3.connect('arduino_data.db')
cursor = conn.cursor()

# Configuração do pandapower
net = pp.create_empty_network()
pp.create_bus(net, vn_kv=0.4)
pp.create_load(net, 0, p_mw=0.1, q_mvar=0.05)

# Função para ler dados do Arduino
def read_arduino_data():
    data = arduino.readline().decode('utf-8').strip().split(';')
    led_status = [int(x) for x in data[0].split(':')[1].split(',')]
    voltage = float(data[1].split(':')[1])
    return led_status + [voltage]

# Função para salvar dados no SQLite
def save_to_sqlite(data):
    cursor.execute('''
        INSERT INTO arduino_data (led1, led2, led3, voltage)
        VALUES (?, ?, ?, ?)
    ''', data)
    conn.commit()

# Função para processar dados com pandapower
def process_with_pandapower(voltage):
    net.bus['vn_kv'] = voltage / 1000
    pp.runpp(net)
    return net.res_bus.vm_pu[0], net.res_load.p_mw[0], net.res_load.q_mvar[0]

# Função para salvar resultados do pandapower
def save_pandapower_results(results):
    cursor.execute('''
        INSERT INTO pandapower_results (bus_voltage, active_power, reactive_power)
        VALUES (?, ?, ?)
    ''', results)
    conn.commit()

# Configuração do Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1('Arduino e pandapower Dashboard'),
    dcc.Graph(id='live-graph-arduino', animate=True),
    dcc.Graph(id='live-graph-pandapower', animate=True),
    dcc.Interval(
        id='graph-update',
        interval=1*1000  # em milissegundos
    ),
])

@app.callback(
    [Output('live-graph-arduino', 'figure'),
     Output('live-graph-pandapower', 'figure')],
    [Input('graph-update', 'n_intervals')]
)
def update_graph(n):
    # Ler e processar dados
    arduino_data = read_arduino_data()
    save_to_sqlite(arduino_data)
    pp_results = process_with_pandapower(arduino_data[3])
    save_pandapower_results(pp_results)

    # Recuperar dados do SQLite para plotagem
    cursor.execute("SELECT * FROM arduino_data ORDER BY timestamp DESC LIMIT 100")
    arduino_df = pd.DataFrame(cursor.fetchall(), columns=['id', 'timestamp', 'led1', 'led2', 'led3', 'voltage'])
    
    cursor.execute("SELECT * FROM pandapower_results ORDER BY timestamp DESC LIMIT 100")
    pp_df = pd.DataFrame(cursor.fetchall(), columns=['id', 'timestamp', 'bus_voltage', 'active_power', 'reactive_power'])

    # Criar gráficos
    arduino_fig = go.Figure()
    arduino_fig.add_trace(go.Scatter(x=arduino_df['timestamp'], y=arduino_df['voltage'], mode='lines+markers', name='Voltage'))
    arduino_fig.update_layout(title='Arduino Data', xaxis_title='Time', yaxis_title='Voltage')

    pp_fig = go.Figure()
    pp_fig.add_trace(go.Scatter(x=pp_df['timestamp'], y=pp_df['bus_voltage'], mode='lines+markers', name='Bus Voltage'))
    pp_fig.add_trace(go.Scatter(x=pp_df['timestamp'], y=pp_df['active_power'], mode='lines+markers', name='Active Power'))
    pp_fig.add_trace(go.Scatter(x=pp_df['timestamp'], y=pp_df['reactive_power'], mode='lines+markers', name='Reactive Power'))
    pp_fig.update_layout(title='pandapower Results', xaxis_title='Time', yaxis_title='Values')

    return arduino_fig, pp_fig

if __name__ == '__main__':
    app.run_server(debug=True)