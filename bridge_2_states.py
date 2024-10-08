import serial
print(serial.__file__)
import serial.tools.list_ports
import socket

import configparser
import requests
import paho.mqtt.client as mqtt
import time
import logging
import json

# Configura il logging
logging.basicConfig(filename='bridge.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Bridge():

	def __init__(self, port):
		self.config = configparser.ConfigParser()
		self.config.read('config.ini')
		self.buffer = []
		self.datiZona = {}
		self.zona = ""
		self.id = ""
		self.currentstate0 = 0
		self.currentstate1 = 0
		self.ser = None
		self.port = port
		self.lat = ""
		self.lon = ""
		self.bowl_data_sent = False
		# Limit for the water Bowl
		# self.sogliaMax = 0.1
		self.sogliaBassa0 = 300	#no water in bowl
		self.sogliaAlta0 = 160	#water in bowl
		self.sogliaBassa1 = 740	#no water in tank
		self.sogliaAlta1 = 415	#water in tank
		self.setupSerial(port)
		self.setupMQTT()
 
	''' OLD
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
 	'''
  
	def setupSerial(self, port):
		try:
			print(f"Impostazione della connessione seriale sulla porta {port.device}")
			
			# Inizializza la seriale
			self.ser = serial.Serial(port.device, 9600, timeout=2)
			time.sleep(2)  # Aspetta che la connessione si stabilizzi

			# Scrivi il messaggio di connessione (esempio: \xff come segnale di inizio)
			self.ser.write(b'\xff')
			
			# Attendi la risposta dall'Arduino (esempio: \xfe come conferma di connessione)
			response = self.ser.read()
			
			if response == b'\xfe':
				print(f"Arduino connesso correttamente sulla porta {port.device}")
				
				# Ora attendiamo che l'Arduino invii la conferma di avvenuta connessione
				print("Connessione riuscita. Pronto a inviare i dati della ciotola.")
				self.portName = port.device
				return True
			else:
				# Gestione degli errori: se la risposta non è corretta
				error = self.ser.read(27)  # Leggi eventuali errori (può variare)
				print(f"Errore: {error}")
				
				# Chiudi la connessione se ci sono problemi
				self.ser.close()
				print('Errore nella connessione seriale con Arduino')
				return False

		except (OSError, serial.SerialException) as e:
			print(f"Errore nell'impostazione della connessione seriale: {e}")
			return False

	#NEW!!!	
	def send_bowl_data(self, zone, id, lat, lon):
		"""
		Invia i dati della ciotola (zona, ID, latitudine e longitudine) all'Arduino
		"""
	
		if self.ser and self.ser.is_open:
			try:
				self.ser.write(b'\xff')
				response = self.ser.read()
			
				if response == b'\xfe':
					# Invia i dati della ciotola
					self.ser.write(zone.encode() + b'\n')
					self.ser.write(id.encode() + b'\n')
					self.ser.write(lat.encode() + b'\n')
					self.ser.write(lon.encode() + b'\n')
					logging.debug(f"Dati inviati all'Arduino: {zone}, {id}, {lat}, {lon}")

				# Attendi la conferma dall'Arduino
				response = self.ser.read()
				if response == b'\x01':
					logging.debug("Arduino ha confermato la ricezione dei dati.")
					self.bowl_data_sent = True  # Imposta il flag a True
					return True
				else:
					print(f"Errore nella conferma dall'Arduino: {response}")
					return False
			except serial.SerialException as e:
				print(f"Errore durante l'invio dei dati all'Arduino: {e}")
				return False
		else:
			print("Connessione seriale non aperta.")
			return False


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
		logging.debug("Connected with result code " + str(rc))

		# Subscribing in on_connect() means that if we lose the connection and
		# reconnect then subscriptions will be renewed.
		#self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Coord") # used for configuration
		self.clientMQTT.subscribe("config/")
		#self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Lvlsensor_0") # water level in the bowl
		#self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Lvlsensor_1") # water level in the tank
		#self.clientMQTT.subscribe(self.zona + '/+/Lvlsensor_1') # tank level in the area
  
		# configuration step
		#self.clientMQTT.publish(self.zona + '/' + self.id + '/' + "Coord", self.lat + '/' + self.lon)
		#self.clientMQTT.publish(f"config/{self.zona}/{self.id}/Coord/{self.lat}/{self.lon}")


	# The callback for when a PUBLISH message is received from the server.
	def on_message(self, client, userdata, msg):
		hostname = socket.gethostname()
		IPAddr = socket.gethostbyname(hostname)
		#if msg.topic == self.zona + '/' + self.id + '/' + "Coord":
		#	payload = str(msg.payload.decode()).split('/')
		#	url = f"http://{IPAddr}/config/{msg.topic}/{payload[0]}/{payload[1]}"
		if msg.topic == "config/topic":
			try:
				# Decodifica il payload JSON in un dizionario
				payload = json.loads(msg.payload.decode())
				logging.debug(f"PAYLOAD: {payload}")
				
				# Verifica che i campi esistano nel payload
				if all(key in payload for key in ('zona', 'id', 'latitudine', 'longitudine')):
					# Estrai i valori dal payload
					self.zona = payload['zona']
					self.id = payload['id']
					self.lat = payload['latitudine']
					self.lon = payload['longitudine']
					
					# Chiama il metodo per inviare i dati della bowl
					self.send_bowl_data(self.zona, self.id, self.lat, self.lon)
				else:
					print("Errore: campi mancanti nel payload")
			except json.JSONDecodeError:
				print("Errore nella decodifica del payload JSON")
			except Exception as e:
				print(f"Errore inatteso: {e}")
   
			#CREATE TOPIC
			self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Lvlsensor_0") # water level in the bowl
			self.clientMQTT.subscribe(self.zona + '/' + self.id + '/' + "Lvlsensor_1") # water level in the tank
			self.clientMQTT.subscribe(self.zona + '/+/Lvlsensor_1') # tank level in the area
			self.clientMQTT.publish(f"config/{self.zona}/{self.id}/Coord/{self.lat}/{self.lon}")

			logging.debug(f"Zona: {self.zona}, ID: {self.id}, Lat: {self.lat}, Lon: {self.lon}")

			url = f"http://{IPAddr}/config/{self.zona}/{self.id}/Coord/{self.lat}/{self.lon}"

		elif msg.topic == self.zona + '/' + self.id + '/' + "Lvlsensor_0":
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
						#futurestate0 = 2	#fill bowl
						futurestate0 = 0    #water in bowl
					else:
						futurestate0 = 1	#no water
						
				#STATE 2
				#elif self.currentstate0 == 2:
				#	if bowlWater == 0.5:
				#		self.ser.write(b'S')
				#		futurestate0 = 0	#water in bowl
				#	else:
				#		futurestate0 = 2	#fill water
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
  
	

		
  
  
  
''' OLD
  		# Gestione dei messaggi delle coordinate
		elif msg.topic == self.zona + '/' + self.id + '/' + "Coord":
			payload = str(msg.payload.decode()).split('/')
			self.lat, self.lon = payload[0], payload[1]
			print(f"Received coordinates: Lat: {self.lat}, Lon: {self.lon} on topic {msg.topic}")
			# Invia le coordinate all'Arduino tramite la seriale
			if self.ser:
				try:
					config_message = f"{self.zona},{self.id},{self.lat},{self.lon}\n"
					self.ser.write(config_message.encode())
					print(f"Inviato all'Arduino: Zona: {self.zona} ID: {self.id} Lat: {self.lat}, Lon: {self.lon}")
				except serial.SerialException as e:
					print(f"Error sending data to Arduino: {e}")
			
			url = f"http://{IPAddr}/config/{msg.topic}/{self.lat}/{self.lon}"'''