import datetime
import pickle
from flask import Flask
from flask import render_template
from flask_swagger import swagger
from flask import jsonify
from flask_swagger_ui import get_swaggerui_blueprint
import holidays
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import configparser

import requests

appname = "IOT - sample1"
app = Flask(appname)
config = configparser.ConfigParser()
config.read('config.ini')
client = influxdb_client.InfluxDBClient(url=config.get("InfluxDBClient","Url"),
   token=config.get("InfluxDBClient","Token"),
   org=config.get("InfluxDBClient","Org"))

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/spec'  # Our API url (can of course be a local resource)

@app.errorhandler(404)
def page_not_found(error):
    return 'Errore pagina non trovata', 404

@app.route('/')
def testoHTML():
    return render_template('main.html')


@app.route('/lista/<sensor>', methods=['GET'])
def stampalista(sensor):
    """
    Print the list
    ---
    parameters:
        - in: path
          name: sensor
          description: arg
          required: true
    responses:
      200:
        description: List
    """
    query_api = client.query_api()
    query = f'from(bucket:"{config.get("InfluxDBClient","Bucket")}")\
    |> range(start: -1h)\
    |> filter(fn:(r) => r._measurement == "new_measurement")\
    |> filter(fn:(r) => r.sensor == "{sensor}")\
    |> filter(fn:(r) => r._field == "value")'
    result = query_api.query(org=config.get("InfluxDBClient","Org"), query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append((record.get_value(), record.get_time()))
    return render_template('lista3.html', lista=results)

@app.route('/newdata/<sensor>/<value>', methods=['POST'])
def addinlista(sensor, value):
    """
    Add element to the list
    ---
    parameters:
        - in: path
          name: sensor
          description: arg
          required: true
        - in: path
          name: value
          description: integer
          required: true
    responses:
      200:
        description: List
    """
    write_api = client.write_api(write_options=SYNCHRONOUS)
    measure = influxdb_client.Point("new_measurement").tag("sensor", sensor).field("value", float(value))
    write_api.write(bucket=config.get("InfluxDBClient","Bucket"), org=config.get("InfluxDBClient","Org"), record=measure)
    return "Data added"

@app.route('/previsione/<ora>', methods=['GET'])
def previsione(ora, lat=44.64, lon=10.92):
    """
    Makes a prediction based on an input hour
    ---
    parameters:
        - in: path
          name: ora
          description: arg
          required: true
        - in: path
          name: lat
          description: float
          required: false
        - in: path
          name: lon
          description: float
          required: false
    responses:
      200:
        description: Int
    """
    # lat e lon di default sono quelle di MODENA
    with open('regressor.pickle', 'rb') as f:
        regressor = pickle.load(f)

        # Ottieni l'ora corrente
        now = datetime.datetime.now()

        # Ottieni le condizioni meteorologiche correnti da un API meteo
        api_key = '7709f02753c2a737ab142230c07b181d'
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}'
        response = requests.get(url)
        weather_data = response.json()
        # Ottieni la stagione in base al mese corrente
        if 3 <= now.month <= 5:
            season = 1  # Spring
        elif 6 <= now.month <= 8:
            season = 2  # Summer
        elif 9 <= now.month <= 11:
            season = 3  # Fall
        else:
            season = 4  # Winter
        yr = now.year - 2011  # 0 per il 2011, 1 per il 2012
        mnth = now.month
        hr = now.hour
        # Crea un oggetto "Italy" che rappresenta le festività italiane
        it_holidays = holidays.IT()

        # Verifica se oggi è festività in Italia
        if datetime.date(now.year, now.month, now.day) in it_holidays:
            holiday = 1
        else:
            holiday = 0
        weekday = now.weekday()
        # Verifica se oggi è un giorno lavorativo
        if weekday < 5:  # 5 corrisponde a sabato, 6 a domenica
            workingday = 0
        else:
            workingday = 1
        # Ottieni il codice weathersit dalle condizioni meteorologiche
        if weather_data['weather'][0]['main'] in ['Clear','Few clouds','Partly cloudy']:
            weathersit = 1 
        elif weather_data['weather'][0]['main'] in ['Cloudy','Mist + Broken clouds','Few clouds','Mist']:
            weathersit = 2
        elif weather_data['weather'][0]['main'] in ['Light Snow','Light Rain']:
            weathersit = 3
        else:
            weathersit = 4
        temp = weather_data['main']['temp'] - 273.15  # Converti da Kelvin a Celsius
        atemp = weather_data['main']['feels_like'] - 273.15  # Converti da Kelvin a Celsius
        hum = weather_data['main']['humidity']

        # Effettua la predizione utilizzando il modello e i dati di input
        predizione = regressor.predict([[season, yr, mnth, hr, holiday, weekday, workingday, weathersit, temp, atemp, hum]])

        # Ritorna la predizione
        return f'La previsione del numero di biciclette utilizzate alle {now} è {int(predizione[0])}'


@app.route("/spec")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "My API"
    
    return jsonify(swag)

if __name__ == '__main__':
    port = 80
    interface = '0.0.0.0'
    
    # Call factory function to create our blueprint
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
        API_URL,
        config={  # Swagger UI config overrides
            'app_name': "Test application"
        }
    )
    app.register_blueprint(swaggerui_blueprint)
    app.run(host=interface,port=port)