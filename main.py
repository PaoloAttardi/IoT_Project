import json
import configparser
import influxdb_client
import datetime
import requests

from flask import Flask, request
from flask import render_template
from flask_swagger import swagger
from flask import jsonify
from utils import newPrediction, BucketList, get_weather_forecast, Bowl
from flask_swagger_ui import get_swaggerui_blueprint
from influxdb_client.client.write_api import SYNCHRONOUS

appname = "Happy Bowls"
app = Flask(appname)
config = configparser.ConfigParser()
config.read('config.ini')
client = influxdb_client.InfluxDBClient(url=config.get("InfluxDBClient","Url"),
   token=config.get("InfluxDBClient","Token"),
   org=config.get("InfluxDBClient","Org"))
activeBowls = BucketList()

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/spec'  # Our API url (can of course be a local resource)

@app.errorhandler(404)
def page_not_found(error):
    return 'Errore pagina non trovata', 404

@app.route('/')
def testoHTML():

    return render_template('homepage.html', devices=activeBowls)


@app.route('/lista/<zone>/<id>', methods=['GET'])
def stampalista(zone, id):
    """
    Print the list
    ---
    parameters:
        - in: path
          name: zone
          description: arg
          required: true
        - in: path
          name: id
          description: arg
          required: true
    responses:
      200:
        description: List
    """
    bowl = activeBowls[zone + '/' + id]
    bowl.loadData()
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={bowl.lat}&lon={bowl.lon}&appid={config.get("OpenWeather","api_key")}&units=metric'
    response = requests.get(url)
    weather_data = response.json()
    today = datetime.datetime.now()
    forecast = get_weather_forecast(config.get("OpenWeather","api_key"),config.get("DEFAULT","lat"),config.get("DEFAULT","lon"))
    return render_template('sensor_details.html', bowl=bowl, devices=activeBowls, weather_data=weather_data, today=today, forecast=forecast)

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
    bowl = activeBowls[sensor + '/' + id]
    write_api = client.write_api(write_options=SYNCHRONOUS)
    measure = influxdb_client.Point(sensor).tag("sensor", type).tag("lat", bowl.lat).tag("lon", bowl.lon).field(id, float(value))
    write_api.write(bucket=config.get("InfluxDBClient","Bucket"), org=config.get("InfluxDBClient","Org"), record=measure)
    return "Data added"
  
@app.route('/config/<zone>/<id>/Coord/<lat>/<lon>', methods=['POST'])
def bowlConfig(zone, id, lat, lon):
    """
    Configure the active buckets
    ---
    parameters:
        - in: path
          name: zone
          description: arg
          required: true
        - in: path
          name: id
          description: arg
          required: true
        - in: path
          name: lat
          description: float
          required: true
        - in: path
          name: lon
          description: float
          required: true
    responses:
      200:
        description: List
    """
    confBowl = Bowl(zone, id, lat, lon)
    if confBowl.id not in activeBowls:
      activeBowls[confBowl.id] = confBowl
    return f"Bowl {confBowl.id} configured"

@app.route('/flusso', methods=['GET'])
def flussoPersone():
    """
    Makes a prediction based on an input hour
    ---
    responses:
      200:
        description: Int
    """
    hour = int(request.args.get('hour'))
    now = datetime.datetime.now()
    predizione = newPrediction(config.get("DEFAULT","lat"),config.get("DEFAULT","lon"),now,hour)
    # Ritorna la predizione
    return f'La previsione del numero di persone alle {hour} è {predizione}'

@app.route('/lista', methods=['GET'])
def listaJSON():
    """
    Return the JSON with the available bowls
    ---
    responses:
      200:
        description: JSON
    """
    table = BucketList()
    for __,bowl in table.items():
      bowl.loadData()
    bowls_dicts = [bowl.to_dict() for __,bowl in table.items()]
    return json.dumps(bowls_dicts)
  
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
    app.run(host=interface,port=port,debug=True)