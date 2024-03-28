from flask import Flask
from flask import render_template
from flask_swagger import swagger
from flask import jsonify
from previsione import newPrediction, BucketList, get_weather_forecast
from flask_swagger_ui import get_swaggerui_blueprint
from influxdb_client.client.write_api import SYNCHRONOUS

import configparser
import influxdb_client
import datetime
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
    table = BucketList(config,client)
    return render_template('homepage.html', devices=table)


@app.route('/lista/<zone>/<sensor>', methods=['GET'])
def stampalista(zone, sensor):
    """
    Print the list
    ---
    parameters:
        - in: path
          name: zone
          description: arg
          required: true
        - in: path
          name: sensor
          description: arg
          required: true
    responses:
      200:
        description: List
    """
    table = BucketList(config,client)
    query = f'from(bucket:"{config.get("InfluxDBClient","Bucket")}")\
    |> range(start: -20)\
    |> filter(fn:(r) => r._measurement == "{zone}")\
    |> filter(fn:(r) => r._field == "{sensor}")'
    result = client.query_api().query(org=config.get("InfluxDBClient","Org"), query=query)
    results1 = []
    results2 = []
    index = ""
    for res in result:
        for record in res.records:
            i += 1
            results1.append(int(record.get_value()))
            results2.append(record.get_time().strftime('%H:%M:%S'))
            index = index + str(i) + ','
    return render_template('sensor_details.html', values=results1, timestamp=results2, devices=table, labels=index)

@app.route('/newdata/<sensor>/<id>/<type>/<value>', methods=['POST'])
def addinlista(sensor, id, type, value):
    """
    Add element to the list
    ---
    parameters:
        - in: path
          name: sensor
          description: arg
          required: true
        - in: path
          name: id
          description: arg
          required: true
        - in: path
          name: type
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
    measure = influxdb_client.Point(sensor).tag("sensor", type).field(id, float(value))
    write_api.write(bucket=config.get("InfluxDBClient","Bucket"), org=config.get("InfluxDBClient","Org"), record=measure)
    return "Data added"

@app.route('/flusso', methods=['GET'])
def flussoPersone():
    """
    Makes a prediction based on an input hour
    ---
    parameters:
        - in: path
          name: ora
          description: arg
          required: true
    responses:
      200:
        description: Int
    """
    hour = requests.get('hour')
    # Ottieni l'ora corrente
    now = datetime.datetime.now()
    predizione = newPrediction(config.get("DEFAULT","lat"),config.get("DEFAULT","lon"),now,hour)
    # Ritorna la predizione
    return f'La previsione del numero di persone alle {hour} è {int(predizione[0])}'
  
@app.route('/previsione')
def previsione():
    table = BucketList(config,client)
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={config.get("DEFAULT","lat")}&lon={config.get("DEFAULT","lon")}&appid={config.get("OpenWeather","api_key")}'
    response = requests.get(url)
    weather_data = response.json()
    weather_data['main']['temp'] = int(weather_data['main']['temp'])
    today = datetime.datetime.now()
    forecast = get_weather_forecast(config.get("OpenWeather","api_key"),config.get("DEFAULT","lat"),config.get("DEFAULT","lon"))
    # days = [(today + datetime.timedelta(days=i)).strftime("%A") for i in range(1, 8)]
    return render_template('weatherpage.html', devices=table, weather_data=weather_data, today=today, forecast=forecast)

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