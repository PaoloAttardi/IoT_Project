#include <Servo.h>

unsigned long previousMillis = 0;
const int interval = 10000;
unsigned long servoOpenTime = 0;
const unsigned long servoDuration = 5000; // 5 secondi per il servo


//bool config = true;
bool setservo = true;
char SoL = '\xff';
char EoL = '\xfe';
// float lat = 10.24;
// float lon = 47.32;

String zona = "";
String id = "";
String lat = "";
String lon = "";
bool config = true;
bool setvalues = true;

Servo servo;

// Definizione degli stati
enum State {
  STATE_CLOSED,  // Tappo chiuso
  STATE_OPEN,    // Tappo aperto
  STATE_FILLING  // In fase di riempimento
};

State currentState = STATE_CLOSED;  // Stato iniziale

// WATER SENSOR
int sensorPin0 = A0;  // Pin analogico dove è collegato il sensore

int sensorValue0 = 0;
float bowlWater = 0.0;   // Variabile per memorizzare il valore letto dal sensore
int sogliaAlta0 = 115;  // Valore per alta presenza di acqua
int sogliaBassa0 = 195; // Valore per bassa presenza di acqua

// CAPACITIVE SOIL SENSOR
int sensorPin1 = A1;  // Pin analogico dove è collegato il sensore

float tankCap = 0.0;  // Variabile per memorizzare il valore letto dal sensore
int sensorValue1 = 0;
int sogliaAlta1 = 415;  // Valore per alta presenza di acqua
int sogliaBassa1 = 740; // Valore per bassa presenza di acqua

int countDigits(float number) {
  char buffer[15];  // Allocate a buffer to hold the string representation

  // Convert float to string
  dtostrf(number, 4, 2, buffer);  // 4 is the total width including decimal point and 2 is the number of digits after the decimal point
  int length = strlen(buffer);
  
  return length;
}



void setup() {
  Serial.begin(9600);  // Aumenta la velocità della porta seriale // Inizializza la comunicazione seriale a 9600 baud

  servo.attach(8);
  // Starting point 
  servo.write(90);
  //delay(2000);
  
  currentState = STATE_CLOSED;
}


void loop() {

  //OLD
  // while (config) {
  //   if (Serial.available() > 0) {
  //     char start = Serial.read();
  //     if (start == SoL) {
  //       Serial.print(EoL);  // Connessione al bridge
  //       Serial.print(lat);  // Passiamo informazioni come coordinate, ID e zona
  //       Serial.print(lon);
  //       char zona[] = "zona_1";
  //       int zona_size = strlen(zona);
  //       char id[] = "002";
  //       int id_size = strlen(id);
  //       Serial.print(zona_size);
  //       Serial.print(zona);
  //       Serial.print(id_size);
  //       Serial.print(id);
  //       config = false;
  //     }       
  //   }
  // }

  while (config) {
    if (Serial.available() > 0) {
      char start = Serial.read();
      if (start == SoL) {
        Serial.print(EoL);
        config = false;
      }
    }
  }

  while (setvalues){
    if(Serial.available() > 0){
      char start2 = Serial.read();
      if (start2 == SoL){
        Serial.print(EoL);
        zona = Serial.readStringUntil('\n');
        id = Serial.readStringUntil('\n');
        lat = Serial.readStringUntil('\n');
        lon = Serial.readStringUntil('\n');

        //Serial.print(zona);
        //Serial.print("ID : ");
        //Serial.print(id);
        //Serial.print(lat);
        //Serial.print(lon);
        
        Serial.write(0x01);
        setvalues = false;
      }
    }
  }

  //if(Serial.available() > 0){
  //  char addnewBowl = Serial.read();
  //  if (addnewBowl == SoL){
  //    config = true;
  //    setvalues = true;
  //  }
  //}
  

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // BOWL --> LvlSensor_0
    int sensorValue0 = analogRead(sensorPin0);
    if (sensorValue0 <= sogliaAlta0) bowlWater = 1.0;
    else if (sensorValue0 >= sogliaBassa0) bowlWater = 0.0;
    else bowlWater = 0.5;

    int pack_size_0 = countDigits(bowlWater);

    
    Serial.print(SoL);
    Serial.print(pack_size_0);
    Serial.print(bowlWater);
    Serial.print("Lvlsensor_0");
    Serial.print(EoL);
     

    // TANK --> LvlSensor_1
    float tankCap = 0.0;
    int sensorValue1 = analogRead(sensorPin1);
    if (sensorValue1 <= sogliaAlta1) tankCap = 1.0;
    else if (sensorValue1 >= sogliaBassa1) tankCap = 0.0;
    else tankCap = 0.5;

    int pack_size_1 = countDigits(tankCap);

    Serial.print(SoL);
    Serial.print(pack_size_1);
    Serial.print(tankCap);
    Serial.print("Lvlsensor_1");
    Serial.print(EoL);
  }

  if (Serial.available() > 0) {
    char val = Serial.read();
    if (currentState == STATE_CLOSED && val == 'A') {
      currentState = STATE_OPEN;
    }
  }
  
  if (currentState == STATE_OPEN) {
    servo.write(0);  // Apri il servo
    servoOpenTime = millis();  // Memorizza l'ora di apertura del servo
    currentState = STATE_FILLING;  // Passa allo stato di riempimento
  }

  if (currentState == STATE_FILLING && (millis() - servoOpenTime >= servoDuration)) {
    servo.write(90);  // Chiudi il servo dopo 5 secondi
    currentState = STATE_CLOSED;  // Torna allo stato chiuso
  }


}

