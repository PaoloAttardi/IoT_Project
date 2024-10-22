import paho.mqtt.client as mqtt

# Callback quando la connessione è stabilita
def on_connect(client, userdata, flags, rc, properties):
    print(f"Connessione stabilita con codice: {rc}")
    # Sottoscrivi a un topic di esempio
    client.subscribe("config/topic")

# Callback quando un messaggio è ricevuto
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Messaggio ricevuto: {msg.topic} -> {payload}")


# Crea un'istanza del client MQTT
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

# Assegna le callback
client.on_connect = on_connect
client.on_message = on_message

# Connessione al broker
try:
    client.connect("test.mosquitto.org", 1883, 60)
except Exception as e:
    print(f"Errore di connessione: {e}")
    exit(1)

# Invia un messaggio di esempio
client.publish("config/topic", "Ciao dal client MQTT!", qos=1)

# Loop per gestire la comunicazione
client.loop_start()

# Mantieni il programma in esecuzione per un po' per ricevere messaggi
try:
    input("Premi Invio per terminare...")
finally:
    client.loop_stop()
    client.disconnect()
