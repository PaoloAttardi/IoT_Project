#include <Servo.h>


unsigned long previousMillis = 0;
const int interval = 10000;
int currentstate;
bool config = true;
bool setservo = true;
char SoL = '\xff';
char EoL = '\xfe';
float lat = 10.24;
float lon = 47.32;

Servo servo;



//WATER SENSOR

int sensorPin0 = A0;    // Pin analogico dove è collegato il sensore

int sensorValue0 = 0;
float bowlWater = 0.0;   // Variabile per memorizzare il valore letto dal sensore
int sogliaAlta0 = 160;  // Valore per alta presenza di acqua
int sogliaBassa0 = 300; // Valore per bassa presenza di acqua

//CAPACITIVE SOIL SENSOR
int sensorPin1 = A1;    // Pin analogico dove è collegato il sensore

float tankCap = 0.0;   // Variabile per memorizzare il valore letto dal sensore
int sensorValue1 = 0;
int sogliaAlta1 = 415;  // Valore per alta presenza di acqua
int sogliaBassa1 = 740; // Valore per bassa presenza di acqua


int countDigits(float number) {
  char buffer[15]; // Allocate a buffer to hold the string representation

  // Convert float to string
  dtostrf(number, 4, 2, buffer); // 4 is the total width including decimal point and 2 is the number of digits after the decimal point
  int length = strlen(buffer);
  
  return length;
}

// int countDigits(int number) {
//   char buffer[15]; // Allocare un buffer sufficiente a contenere l'intero come stringa, inclusi segno e terminatore null

//   // Converti l'intero in stringa
//   itoa(number, buffer, 10); // 10 indica la base decimale
//   int length = strlen(buffer);
  
//   return length;
// }


void setup() {
  Serial.begin(9600); // Inizializza la comunicazione seriale a 9600 baud

  servo.attach(8);
  //starting point --> filo tirato
  servo.write(90);
  delay(2000);
  

  currentstate = 0;
}

void sendData(float value, const char* sensorName) {
  int pack_size = countDigits(value);
  Serial.print(SoL);
  Serial.print(pack_size);
  Serial.print(value, 2); // Specifica il numero di decimal
  Serial.print(sensorName);
  Serial.print(EoL);
}


void loop() {

  while (config) {
    if (Serial.available() > 0){
      char start = Serial.read();
      if (start == SoL){
        Serial.print(EoL); // connessione al bridge
        Serial.print(lat); // passiamo informazioni come coordinate, id e zona
        Serial.print(lon);
        char zona[] = "zona_1";
        int zona_size = strlen(zona);
        char id[] = "001";
        int id_size = strlen(id);
        Serial.print(zona_size);
        Serial.print(zona);
        Serial.print(id_size);
        Serial.print(id);
        config = false;
      }       
    }
  }

  while (setservo){
    servo.write(90);
    delay(100);
    setservo = false;
  }


 unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    //BOWL --> LvlSensor_0
    sensorValue0 = analogRead(sensorPin0);

    
    if(sensorValue0 <= sogliaAlta0) bowlWater = 1.0;
    else if (sensorValue0 >= sogliaBassa0) bowlWater = 0.0;
    else bowlWater = 0.5;
    
    int pack_size_0 = countDigits(bowlWater);

    // Serial.println("Sending Lvlsensor_0 data...");
    Serial.print(SoL);
    Serial.print(pack_size_0);
    Serial.print(bowlWater);
    Serial.print("Lvlsensor_0");
    Serial.print(EoL);
    // Serial.println("Lvlsensor_0 data sent");

       


    //TANK --> LvlSensor_1
    sensorValue1 = analogRead(sensorPin1);
    if(sensorValue1 <= sogliaAlta1) tankCap = 1.0;
    else if (sensorValue1 >= sogliaBassa1) tankCap = 0.0;
    else tankCap = 0.5;
  
    int pack_size_1 = countDigits(tankCap);
 

    // Serial.println("Sending Lvlsensor_1 data...");
    Serial.print(SoL);
    Serial.print(pack_size_1);
    Serial.print(tankCap);
    Serial.print("Lvlsensor_1");
    Serial.print(EoL);
    // Serial.println("Lvlsensor_1 data sent");
    
  




  if (Serial.available() > 0) {
    char val = Serial.read();

    int futurestate = currentstate;
    if (currentstate == 0 && val == 'A') {
      futurestate = 1;  // acceso
    } else if (currentstate == 1 && val == 'S') {
      futurestate = 0;  // spento
    }

    if (currentstate != futurestate) {
      if (futurestate == 1) {
        servo.write(0);  // open water flow
        //delay(4000);
      } else if (futurestate == 0) {
        Serial.println("Closing water flow...");
        servo.write(90);  // close water flow
        delay(1000);
      }
      currentstate = futurestate;
    }
  }
  }
  }






