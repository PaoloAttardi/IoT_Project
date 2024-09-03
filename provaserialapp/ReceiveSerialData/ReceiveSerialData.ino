//ReceiveSerialData (Arduino Uno) Chris Ward 02/09/2023

//vars
unsigned long lgUpdateTime;
String lat;
String lng;

void setup()
{
         Serial.begin(9600);
         lgUpdateTime = millis();
}

void loop()
{
         //Excute loop every 2 seconds
	     if(millis() - lgUpdateTime > 2000) 
         {
               lgUpdateTime = millis();
               
               if (Serial.available() > 0)
               {
                    //Read Data From App
                    lat = Serial.readStringUntil('|');
                    lng = Serial.readStringUntil('\n');
               
                    //Send Data to Serial Monitor
                    Serial.println(lat);
                    Serial.println(lng); 
               }
         }
}
