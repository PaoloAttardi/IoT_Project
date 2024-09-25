import serial
import serial.tools.list_ports
from bridge_2_states import Bridge
from main import activeBowls

class Scheduler():

    def __init__(self):
        self.arduini = []
        self.bridges = []

    
    def loop(self):
        while(True):
            print("Checking connection...")
            self.checkConnection()
            for bridge in self.bridges:
                if bridge.ser.isOpen():
                    print(f"Reading data from {bridge.port.device}")
                    bridge.readData()
                else:
                    print(f"Removing bridge on {bridge.port.device}")
                    self.bridges.remove(bridge)
                    self.arduini.remove(bridge.port.device)
                    
                    
    '''NEW       
    def loop(self):
        while True:
            print("Checking connection...")
            self.checkConnection()

            for bridge in self.bridges:
                if bridge.ser.isOpen():
                    # Invia i dati della ciotola solo la prima volta (se il flag è False)
                    if bridge.lat is not None and bridge.lon is not None:  # Controlla se lat e lon sono disponibili
                        if bridge.send_bowl_data(bridge.zona, bridge.id, bridge.lat, bridge.lon):
                            print(f"Dati della ciotola inviati con successo: {bridge.zona}, {bridge.id}, {bridge.lat}, {bridge.lon}")
                        else:
                            print("Errore durante l'invio dei dati all'Arduino.")

                    # Continuare a leggere i dati dopo la configurazione
                    print(f"Reading data from {bridge.port.device}")
                    bridge.readData()
                else:
                    # Rimuovi il bridge se la connessione non è più valida
                    print(f"Removing bridge on {bridge.port.device}")
                    self.bridges.remove(bridge)
                    self.arduini.remove(bridge.port.device)
    ''' 



    
    def checkConnection(self):
        ports = serial.tools.list_ports.comports()
        print(f"Available ports: {[port.device for port in ports]}")
        for port in ports:
            print(f"Checking port {port.device} - {port.description}")
            if 'Arduino Uno' in port.description or 'IOUSBHostDevice' in port.description:
                if port.device not in self.arduini:
                    print(f"Arduino Uno found on {port.device}")
                    self.arduini.append(port.device)
                    self.bridges.append(Bridge(port))
                else:
                    print(f"Arduino Uno on {port.device} already in list")
            else:
                print(f"No Arduino Uno on {port.device}")

    
if __name__ == '__main__':
    sc = Scheduler()
    sc.loop()