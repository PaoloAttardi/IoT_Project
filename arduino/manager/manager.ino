unsigned long previousMillis = 0;
const int interval = 10000;
int currentstate;
bool config = true;

int countDigits(float number) {
  int digitCount = 0;
  
  // Conta le cifre della parte intera
  int integerPart = (int)number;
  while (integerPart > 0) {
    digitCount++;
    integerPart /= 10;
  }
  
  // Conta le cifre della parte frazionaria
  float fractionalPart = number - integerPart;
  if (fractionalPart > 0) {
    digitCount++;  // Conta la virgola decimale
    while (fractionalPart > 0) {
      digitCount++;
      fractionalPart *= 10;
      fractionalPart = fractionalPart - (int)fractionalPart;
    }
    digitCount++;
  }
  
  return digitCount;
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
  char SoL = '\xff';
  char EoL = '\xfe';
  while (config) {
    if (Serial.available() > 0){
      char start = Serial.read();
      if (start == SoL){
        Serial.print(EoL); //connessione al bridge
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
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    Serial.print(SoL);
    float tempValue = random(12, 22);
    int pack_size = countDigits(tempValue);
    Serial.print(pack_size);
    Serial.print(tempValue);
    Serial.print("Tsensor_0");
    Serial.print(EoL);    
  }
  if(Serial.available() > 0){
    char val = Serial.read();

    int futurestate;
    if(currentstate == 0 && val == 'A') futurestate = 1;
    if(currentstate == 1 && val == '1') futurestate = 2; //acceso
    if(currentstate == 2 && val == 'S') futurestate = 3;
    if(currentstate == 3 && val == '1') futurestate = 4; //spento
    if(currentstate == 1 && val == '2') futurestate = 5; //acceso
    if(currentstate == 5 && val == 'S') futurestate = 6;
    if(currentstate == 6 && val == '2') futurestate = 7; //spento

    if(currentstate != futurestate){
      if(futurestate == 2) digitalWrite(13,HIGH);
      if(futurestate == 4) {
        digitalWrite(13,LOW);
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

