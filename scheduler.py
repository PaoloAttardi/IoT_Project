import serial
import serial.tools.list_ports
from bridge_2_states import Bridge

class Scheduler():

    def __init__(self):
        self.arduini = []
        self.bridges = []

    '''OLD
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
    '''
                    
                    
    def loop(self):
        while True:
            print("Checking connection...")
            self.checkConnection()
            
            for bridge in self.bridges:
                if bridge.ser.isOpen():
                    # Invia i dati della ciotola solo la prima volta (se il flag è False)
                    if not bridge.bowl_data_sent:
                        if bridge.send_bowl_data(self.zone, self.bowl_id, self.lat, self.lon):
                            print(f"Dati della ciotola inviati con successo: {self.zone}, {self.bowl_id}, {self.lat}, {self.lon}")
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