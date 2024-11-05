import serial
print(serial.__file__)
import serial.tools.list_ports
import socket

import configparser
import requests
import paho.mqtt.client as mqtt
import time
import logging

# Configura il logging
logging.basicConfig(filename='output_5_9_24.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Bridge():

	def __init__(self, port):
		self.config = configparser.ConfigParser()
		self.config.read('config.ini')
		self.buffer = []
		self.datiZona = {}
		self.currentstate0 = 0
		self.currentstate1 = 0
		self.ser = None
		self.port = port
		self.lat = 0
		self.lon = 0
		# Limit for the water Bowl
		# self.sogliaMax = 0.1
		self.sogliaBassa0 = 300	#no water in bowl
		self.sogliaAlta0 = 160	#water in bowl
		self.sogliaBassa1 = 740	#no water in tank
		self.sogliaAlta1 = 415	#water in tank
		self.setupSerial(port)
		self.setupMQTT()
 
  
	def setupSerial(self, port):        
		try:
			print(f"Setting up serial connection on {port.device}")
			self.ser = serial.Serial(port.device, 9600, timeout=2)
			time.sleep(2)
			# Write the connection message
			self.ser.write(b'\xff')
			# Wait for the responses from the Arduino
			response = self.ser.read()
			if response == b'\xfe':
				print(f"Arduino connesso alla porta {port.device}")
				# leggi informazioni sulle coordinate
				self.lat = str(self.ser.read(5).decode())
				self.lon = str(self.ser.read(5).decode())
				# leggi informazioni sulla zona della ciotola
				size_zona = int(self.ser.read().decode())
				self.zona = self.ser.read(size_zona).decode()
				# leggi informazioni sull'id
				size_id = int(self.ser.read().decode())
				self.id = self.ser.read(size_id).decode()
				self.portName = port.device
				return True
			else:
				error = self.ser.read(27)
				print(f"Error: {error}")
				# If the Arduino doesn't reply correctly, close the connection
				self.ser.close()
				print('Errore nella connessione')
				return False
		except (OSError, serial.SerialException) as e:
			print(f"Serial setup exception: {e}")
			pass


	def setupMQTT(self):
		self.clientMQTT = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
		self.clientMQTT.on_connect = self.on_connect
		self.clientMQTT.on_message = self.on_message
		print("connecting to MQTT broker...")
		self.clientMQTT.connect(
			self.config.get("MQTT","Server", fallback= "broker.hivemq.com"),
			self.config.getint("MQTT","Port", fallback= 1883),
			60)
		self.clientMQTT.loop_start()


	def on_connect(self, client, userdata, flags, rc, properties):
		print("Connected with result code " + str(rc))

		# Subscribing in on_connect() means that if we lose the connection and
		# reconnect then subscriptions will be renewed.
		self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Coord") # used for configuration
		self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Lvlsensor_0") # water level in the bowl
		self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Lvlsensor_1") # water level in the tank
		self.clientMQTT.subscribe(self.zona + '/+/Lvlsensor_1') # tank level in the area
		# configuration step
		self.clientMQTT.publish(self.zona + '/' + self.id + '/' + "Coord", self.lat + '/' + self.lon)

	# The callback for when a PUBLISH message is received from the server.
	def on_message(self, client, userdata, msg):
		hostname = socket.gethostname()
		IPAddr = socket.gethostbyname(hostname)
		if msg.topic == self.zona + '/' + self.id + '/' + "Coord":
			payload = str(msg.payload.decode()).split('/')
			url = f"http://{IPAddr}/config/{msg.topic}/{payload[0]}/{payload[1]}"
		else:
			if msg.topic == self.zona + '/' + self.id + '/' + "Lvlsensor_0":
				payload0 = msg.payload.decode()
				print(f"Received message BOWLWATER: '{payload0}' on topic '{msg.topic}'")
				try:
					# Supponendo che il payload sia un numero intero
					bowlWater = float(payload0)
					# Esegui azioni basate sul valore ricevuto
					print(f"Value received from Lvlsensor_0: {bowlWater}")
				except ValueError:
					print(f"Invalid payload: {payload0}")
				
				futurestate0 = None
				
				#state = 0 --> water in bowl
				#state = 1 --> no water in bowl
				#state = 2 --> filling bowl
				
				#STATE 0
				if self.currentstate0 == 0:	
					if bowlWater == 0.0:
						futurestate0 = 1	#no water in bowl
					else:
						futurestate0 = 0	#water in bowl
				
				#STATE 1
				elif self.currentstate0 == 1:
					url = f'http://{IPAddr}/meteo/{self.lat}/{self.lon}'
					response = requests.get(url)
					if bowlWater == 0.0 and response.text != 'Rainy':
						self.ser.write(b'A')
						futurestate0 = 2	#fill bowl
					else:
						futurestate0 = 1	#no water
						
				#STATE 2
				elif self.currentstate0 == 2:
					if bowlWater == 0.5:
						self.ser.write(b'S')
						futurestate0 = 0	#water in bowl
					else:
						futurestate0 = 2	#fill water
				self.currentstate0 = futurestate0
				
			
			elif msg.topic == self.zona + '/' + self.id + '/' + "Lvlsensor_1":
				payload1 = msg.payload.decode()
				print(f"Received message TANKCAP: '{payload1}' on topic '{msg.topic}'")
				try:
					# Supponendo che il payload sia un numero intero
					tankCap = float(payload1)
					# Esegui azioni basate sul valore ricevuto
					print(f"Value received from Lvlsensor_1: {tankCap}")
				except ValueError:
					print(f"Invalid payload: {payload1}")

				futurestate1 = None
				#STATE 0
				if self.currentstate1 == 0:
					if tankCap == 0.0:
						futurestate1 = 1
					else:
						futurestate1 = 0

				#STATE 1
				elif self.currentstate1 == 1:
					print("Warning: No water in tank!")
					self.currentstate1 = 0
				self.currentstate1 = futurestate1
     
			elif 'Lvlsensor_1' in msg.topic:
				value = float(msg.payload.decode())
				zona, id, name = msg.topic.split('/')
				if self.id != id:
					self.datiZona[id] = value
			url = f"http://{IPAddr}/newdata/{msg.topic}/{msg.payload.decode()}"
		if url:
			try:
				print(f"Sending POST request to {url}")
				response = requests.post(url)
				print(f"Response Status Code: {response.status_code}")
				print(f"Response Content: {response.text}")
			except requests.exceptions.RequestException as e:
				print(f"Request exception: {e}")
		"""try:
			print(url)
			requests.post(url)
		except requests.exceptions.RequestException as e:
			raise SystemExit(e)"""

	def readData(self):
		#look for a byte from serial
		while self.ser.in_waiting>0:
			# data available from the serial port
			lastchar=self.ser.read(1)
			time.sleep(0.2) 
			if lastchar==b'\xfe': #EOL
				print("\nValue received")
				self.useData()
				self.buffer = []
			else:
				# append
				self.buffer.append(lastchar)

	def useData(self):
		print(self.buffer)
		# I have received a packet from the serial port. I can use it

		if self.buffer[0] != b'\xff':
			print('Pacchetto errato')
			return False
		numval = int(self.buffer[1].decode()) # legge size del pacchetto
		val = ''
		for i in range (numval):
			val = val + self.buffer[i+2].decode() # legge valore del pacchetto
		sensor_name = ''
		SoN = numval + 2 # Start of Name
		sensorLen = len(self.buffer) - (SoN)
		for j in range (sensorLen):
			sensor_name = sensor_name + str(self.buffer[j + SoN].decode())

		print("Publishing message:")
		print(f"Topic: {self.zona}/{self.id}/{sensor_name}")
		print(f"Payload: {val}")
		
		self.clientMQTT.publish(self.zona + '/' + self.id + '/' + sensor_name, val)
  
	

		