#include <Servo.h>


unsigned long previousMillis = 0;
unsigned long previousMillis1 = 0;
const int interval = 5000;
const int interval1 = 2000;
int currentState;
int lastState;
unsigned long lastChangeTime = 0;
const unsigned long openDelay = 4000; // Tempo per cui il servo rimane aperto (in millisecondi)

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
int sogliaAlta0 = 115;  // Valore per alta presenza di acqua
int sogliaBassa0 = 195; // Valore per bassa presenza di acqua

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
  

  currentState = 1;
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
        char id[] = "002";
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
    
  

  
// if (currentMillis - previousMillis1 >= interval1) {
//     previousMillis1 = currentMillis;

//     if (Serial.available() > 0) {
//       char val = Serial.read();
      
//       if (val == 'A') {
//         currentState = 0;  // Passa allo stato di apertura
//         previousMillis1 = millis();  // Resetta il timer
//       } else if (val == 'S') {
//         currentState = 1;  // Passa allo stato di chiusura
//         previousMillis1 = millis();  // Resetta il timer
//       }
//     }

//     if (currentState != lastState) {
//       switch (currentState) {
//         case 0: // Stato 0: apertura
//           servo.write(0);  // Apri il flusso d'acqua
//           Serial.println("Opening water flow...");
//           break;
//         case 1: // Stato 1: chiusura
//           servo.write(90);  // Chiudi il flusso d'acqua
//           Serial.println("Closing water flow...");
//           break;
//       }
//       lastState = currentState;  // Aggiorna lo stato precedente
//     }
//   }  
// }
// }
  // Gestione dell'input seriale
  if (Serial.available() > 0) {
    char val = Serial.read();

    if (val == 'A') {
      currentState = 0;  // Passa allo stato di apertura
      previousMillis1 = millis();  // Resetta il timer
    } else if (val == 'S') {
      currentState = 1;  // Passa allo stato di chiusura
      previousMillis1 = millis();  // Resetta il timer
    }
  }
  }
  unsigned long currentMillis1 = millis();
  // Gestione dei cambiamenti di stato basati su tempo
    if (currentMillis1 - previousMillis1 >= interval1) {
      previousMillis1 = currentMillis1;

      switch (currentState) {
        case 0: // Stato 0: attesa per apertura
          // Esegui azioni per apertura
          servo.write(0);  // Apri il flusso d'acqua
          Serial.println("Opening water flow...");
          currentState = 1;  // Passa allo stato 1
          break;

        case 1: // Stato 1: attesa per chiusura
          // Esegui azioni per chiusura
          servo.write(90);  // Chiudi il flusso d'acqua
          Serial.println("Closing water flow...");
          currentState = 0;  // Torna allo stato 0
          break;
      }
    }
}





