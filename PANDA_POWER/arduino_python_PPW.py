import serial
import json
import pandapower as pp
from abc import ABC, abstractmethod

class SerialReader:
    def __init__(self, port='/dev/ttyUSB0', baud_rate=9600):
        self.serial = serial.Serial(port, baud_rate)

    def read_data(self):
        return self.serial.readline().decode('utf-8').strip()

class DataParser(ABC):
    @abstractmethod
    def parse(self, data):
        pass

class ArduinoDataParser(DataParser):
    def parse(self, data):
        led_status, voltage = data.split(';')
        led_values = [int(x) for x in led_status.split(':')[1].split(',')]
        voltage_value = float(voltage.split(':')[1])
        return {'led_status': led_values, 'voltage': voltage_value}

class PandaPowerIntegrator:
    def __init__(self):
        self.net = pp.create_empty_network()

    def create_simple_circuit(self, voltage):
        pp.create_bus(self.net, vn_kv=voltage/1000)
        pp.create_load(self.net, 0, p_mw=0.1, q_mvar=0.05)
        pp.runpp(self.net)

    def get_results(self):
        return {
            'voltage_pu': self.net.res_bus.vm_pu[0],
            'loading_percent': self.net.res_line.loading_percent[0] if len(self.net.line) > 0 else None
        }

class JsonGenerator:
    @staticmethod
    def generate(arduino_data, pandapower_data):
        return json.dumps({
            'arduino_data': arduino_data,
            'pandapower_data': pandapower_data
        })

class ArduinoPandaPowerSystem:
    def __init__(self, serial_reader, data_parser, pp_integrator, json_generator):
        self.serial_reader = serial_reader
        self.data_parser = data_parser
        self.pp_integrator = pp_integrator
        self.json_generator = json_generator

    def process_data(self):
        raw_data = self.serial_reader.read_data()
        arduino_data = self.data_parser.parse(raw_data)
        self.pp_integrator.create_simple_circuit(arduino_data['voltage'])
        pp_data = self.pp_integrator.get_results()
        return self.json_generator.generate(arduino_data, pp_data)

if __name__ == "__main__":
    serial_reader = SerialReader()
    data_parser = ArduinoDataParser()
    pp_integrator = PandaPowerIntegrator()
    json_generator = JsonGenerator()

    system = ArduinoPandaPowerSystem(serial_reader, data_parser, pp_integrator, json_generator)

    while True:
        json_output = system.process_data()
        print(json_output)