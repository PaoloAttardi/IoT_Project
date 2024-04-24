unsigned long previousMillis = 0;
const int interval = 10000;
int currentstate;
bool config = true;
char SoL = '\xff';
char EoL = '\xfe';
float lat = 44.64;
float lon = 10.92;
float tankCap = 2.0;
float bowlWater = 0.00;

int countDigits(float number) {
  char buffer[15]; // Allocate a buffer to hold the string representation

  // Convert float to string
  dtostrf(number, 4, 2, buffer); // 4 is the total width including decimal point and 2 is the number of digits after the decimal point
  int length = strlen(buffer);
  
  return length;
}


void setup() {
  // put your setup code here, to run once:
  // 3 pin input sensori e 2 pin in output
  Serial.begin(9600);
  pinMode(13, OUTPUT);
  pinMode(12, OUTPUT);

  currentstate = 0;
}

void loop() {
  // put your main code here, to run repeatedly:
  while (config) {
    if (Serial.available() > 0){
      char start = Serial.read();
      if (start == SoL){
        Serial.print(EoL); // connessione al bridge
        Serial.print(lat); // passiamo informazioni come coordinate, id e zona
        Serial.print(lon);
        char zona[] = "zona_2";
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
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    Serial.print(SoL);
    float drink = random(1, 100);
    if (drink > 60 && bowlWater >= 0.05) { // case where a dog drank from the bowl
      bowlWater = bowlWater - 0.05;
    }
    int pack_size_1 = countDigits(bowlWater);
    Serial.print(pack_size_1);
    Serial.print(bowlWater);
    Serial.print("Lvlsensor_0"); // water in the bowl
    Serial.print(EoL);
    Serial.print(SoL);
    int pack_size_2 = countDigits(tankCap);
    Serial.print(pack_size_2);
    Serial.print(tankCap);
    Serial.print("Lvlsensor_1"); // water in the tank
    Serial.print(EoL); 
  }
  if(Serial.available() > 0){
    char val = Serial.read();

    int futurestate; // probabilmente si può rimuovere il 2
    if(currentstate == 0 && val == 'A') futurestate = 1;
    if(currentstate == 1 && val == '1') futurestate = 2; //acceso
    if(currentstate == 2 && val == 'S') futurestate = 3;
    if(currentstate == 3 && val == '1') futurestate = 4; //spento
    if(currentstate == 1 && val == '2') futurestate = 5; //acceso
    if(currentstate == 5 && val == 'S') futurestate = 6;
    if(currentstate == 6 && val == '2') futurestate = 7; //spento

    if(currentstate != futurestate){
      if(futurestate == 2 && tankCap >= 0.1) {
        digitalWrite(13,HIGH); // open water flow
        bowlWater = bowlWater + 0.1;
        tankCap = tankCap - 0.1;
      }
      if(futurestate == 4) {
        digitalWrite(13,LOW); // close water flow
        futurestate = 0;
      }
      if(futurestate == 5) digitalWrite(12,HIGH);
      if(futurestate == 7) {
        digitalWrite(12,LOW);
        futurestate = 0;
      }
    }
    else{
    	if(currentstate < 2) futurestate = 0;
      if(currentstate >= 2 && currentstate < 4) futurestate = 2;
      if(currentstate >= 5) futurestate = 5;
    }
    
    currentstate = futurestate;
  }
}

