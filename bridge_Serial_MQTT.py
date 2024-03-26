import serial
import serial.tools.list_ports
import socket

import configparser
import requests
import paho.mqtt.client as mqtt
import time

class Bridge():

	def __init__(self, port):
		self.config = configparser.ConfigParser()
		self.config.read('config.ini')
		self.buffer = []
		self.datiZona = {}
		self.currentState = 0
		self.ser = None
		self.port = port
		# valori di soglia per le temperature
		self.sogliaMax = 35
		self.sogliaMin = 10
		self.setupSerial(port)
		self.setupMQTT()
 
  
	def setupSerial(self, port):        
		try:
			# apre la porta seriale
			self.ser = serial.Serial(port.device, 9600, timeout=2)
			time.sleep(2)
			# scrive un messaggio sull'self
			self.ser.write(b'\xff')
			# legge la risposta dell'self
			response = self.ser.read()
			# verifica se l'self ha risposto correttamente
			if response == b'\xfe':
				print(f"Arduino connesso alla porta {port.device}")
				# se l'self è stato trovato aggiungi il suo id al dizionario con il buffer associato, esci dal ciclo
				size_zona = int(self.ser.read().decode())
				self.zona = self.ser.read(size_zona).decode()
				size_id = int(self.ser.read().decode())
				self.id = self.ser.read(size_id).decode()
				print(f'Arduino number: {self.id} of length {size_id} and zone: {self.zona} of length {size_zona}')
				self.portName = port.device
				return True
			else:
				error = self.ser.read(27)
				print(error)
				# se l'self non ha risposto correttamente, chiude la porta seriale
				self.ser.close()
				print('Errore nella connessione')
				return False
		except (OSError, serial.SerialException):
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
		self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Tsensor_0")
		self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "LvLsensor_0")
		self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "LvLsensor_1")
		self.clientMQTT.subscribe(self.zona + '/+/Tsensor_0')

    # The callback for when a PUBLISH message is received from the server.
	def on_message(self, client, userdata, msg):
		print(msg.topic + " " + str(msg.payload))
		if msg.topic == self.zona + '/' + self.id + '/' + "LvLsensor_0":
			if float(msg.payload.decode())<15:
				self.ser.write(b'A0')
			else:
				self.ser.write(b'S0')
		elif msg.topic == self.zona + '/' + self.id + '/' + "Tsensor_0":
			dati = list(self.datiZona.values())
			if len(dati) != 0: media = sum(dati) / len(dati)
			else: media = float(msg.payload.decode()) 
			futureState = None
			if self.currentState == 0:
				if float(msg.payload.decode())>media+1:
					futureState = 1
				elif float(msg.payload.decode())<media-5:
					futureState = 2
				else:
					self.ser.write(b'S1')
			elif self.currentState == 1:
				if float(msg.payload.decode())>self.sogliaMax:
					futureState = 3
				else: futureState = 0
			elif self.currentState == 2:
				if float(msg.payload.decode())<self.sogliaMin:
					futureState = 3
				else: futureState = 0
			elif self.currentState == 3:
				self.ser.write(b'A1')
				futureState = 0
			self.currentState = futureState
		elif msg.topic == self.zona + '/' + self.id + '/' + "LvLsensor_1":
			if float(msg.payload.decode())<15:
					self.ser.write(b'A2')
			else:
				self.ser.write(b'S2')
		elif 'Tsensor_0' in msg.topic:
			value = float(msg.payload.decode())
			zona, id, name = msg.topic.split('/')
			if self.id != id:
				self.datiZona[id] = value
		hostname = socket.gethostname()
		IPAddr = socket.gethostbyname(hostname)
		url = "http://"+IPAddr + "/newdata" + f"/{msg.topic}" + f"/{msg.payload.decode()}"
		try:
			requests.post(url)
		except requests.exceptions.RequestException as e:
			raise SystemExit(e)

	def readData(self):
		#look for a byte from serial
		while self.ser.in_waiting>0:
			# data available from the serial port
			lastchar=self.ser.read(1)
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
		#print(val)
		sensor_name = ''
		SoN = numval + 2
		sensorLen = len(self.buffer) - (SoN)
		for j in range (sensorLen):
			sensor_name = sensor_name + str(self.buffer[j + SoN].decode())
		check = self.clientMQTT.publish(self.zona + '/' + self.id + '/' + sensor_name, val).is_published()
		self.clientMQTT.on_message