import paho.mqtt.client as mqtt
import time
import configparser  # Assicurati di importare questo se stai usando un file di configurazione

# Configurazione del broker
config = configparser.ConfigParser()
config.read('config.ini')  # Assicurati di avere il file di configurazione

#broker = config.get("MQTT", "Server", fallback="broker.hivemq.com")
#port = config.getint("MQTT", "Port", fallback=1883)
topics = ["config/topic", "Soliera/2/Coord", "Soliera/2/Lvlsensor_0", "Soliera/2/Lvlsensor_1", "Soliera/+/Lvlsensor1" ]  # Sostituisci con i topic ai quali vuoi iscriverti

# Variabile globale per tracciare l'ultimo messaggio ricevuto
last_message_time = time.time()
# Tempo di attesa prima di considerare che non ci sono più messaggi (in secondi)
no_message_timeout = 10

# Funzione di connessione al broker
def connect_mqtt():
		try:
			mqtt_client.connect(
				config.get("MQTT","Server", fallback= "broker.hivemq.com"),
				config.getint("MQTT","Port", fallback= 1883),
				60)
			print(f'Connesso a {config.get("MQTT", "Server")}:{config.get("MQTT", "Port")}')
		except Exception as e:
			print(f"Errore nella connessione MQTT: {e}")

# Callback per la connessione
def on_connect(client, userdata, flags, rc, properties):
    print(f"Connesso al broker MQTT con codice di risultato {rc}")
    for topic in topics:
        client.subscribe(topic, qos=0)  # Sottoscrivi ai topic con QoS 0
    mqtt_client.publish(topics[0], "", qos=0, retain=True)

# Callback per la ricezione dei messaggi
def on_message(client, userdata, msg):
    global last_message_time
    last_message_time = time.time()  # Aggiorna il tempo dell'ultimo messaggio ricevuto
    print(f"Messaggio ricevuto su {msg.topic}: {msg.payload.decode()}")

# Creazione del client MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Associazione delle callback
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connessione al broker
connect_mqtt()

# Loop principale per ricevere messaggi
try:
    print("In attesa di messaggi...")
    while True:
        mqtt_client.loop()  # Gestisce la ricezione dei messaggi
        current_time = time.time()
        
        # Controlla se è trascorso il tempo senza messaggi
        if current_time - last_message_time > no_message_timeout:
            print("Nessun messaggio ricevuto negli ultimi 10 secondi. Invio messaggio di stop.")
            last_message_time = current_time  # Reset del timer
            # Qui puoi inviare un messaggio di stop se desideri
            # mqtt_client.publish("your_stop_topic", "Stop message", qos=0)
        
except KeyboardInterrupt:
    print("Disconnessione dal broker...")
    mqtt_client.disconnect()
