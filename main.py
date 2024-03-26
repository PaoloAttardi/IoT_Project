from flask import Flask
from flask import render_template
from flask_swagger import swagger
from flask import jsonify
import requests
from previsione import newPrediction
from flask_swagger_ui import get_swaggerui_blueprint
from influxdb_client.client.write_api import SYNCHRONOUS

import configparser
import influxdb_client
import datetime


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
    query = f'from(bucket:"{config.get("InfluxDBClient","Bucket")}") |> range(start: -120h)'
    tables = client.query_api().query(query)

    # Process the query results
    table = {}
    for tab in tables:
        for row in tab.records:
            val = row.values["_field"]
            zone = row.values["_measurement"]
            if val not in table: table[zone] = row.values["_field"]
    
    return render_template('main.html', devices=table)


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
    query = f'from(bucket:"{config.get("InfluxDBClient","Bucket")}") |> range(start: -120h)'
    tables = client.query_api().query(query)
    i = 0
    # Process the query results
    table = {}
    for tab in tables:
        for row in tab.records:
            val = row.values["_field"]
            zone = row.values["_measurement"]
            if val not in table: table[zone] = row.values["_field"]
    query = f'from(bucket:"{config.get("InfluxDBClient","Bucket")}")\
    |> range(start: -120h)\
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
            results2.append(i)
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

@app.route('/previsione', methods=['GET'])
def previsione(lat=44.64, lon=10.92):
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
    # Ottieni l'ora corrente
    ora = requests.args.get('hour')
    now = datetime.datetime.now()
    predizione = newPrediction(lat,lon,now,ora)
    # Ritorna la predizione
    return f'La previsione del numero di persone alle {now} è {int(predizione[0])}'


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