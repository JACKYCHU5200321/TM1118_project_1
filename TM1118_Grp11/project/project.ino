
Smart IOT Tag to show staff's status
Using ESP8266

This sketch receives a JSON message from the MQTT broker, extracts the
"node_id", and uses the numeric part (xx from Axx) for a condition.

R1: 1st release
R2: Correct client.subscribe inside reconnect()
R3: Modified to display pixel patterns instead of letters.
R4: Modified to draw 11 pixels initially and blink a specific pixel
    based on serial input.
R5: Modified to parse JSON from serial and use node_id for condition.
R6: Modified to receive JSON from MQTT instead of serial.
*******************************************************************************

#include <SPI.h>
#include <ESP8266WiFi.h>        
#include <PubSubClient.h>       
#include <ArduinoJson.h>        
#include <stdlib.h> 

#define NUMBER_OF_DEVICES 1
#define CS_PIN D4

#define red_light_pin D0    
#define green_light_pin D8  
#define blue_light_pin D3   
#define TRIG D2             
#define ID 5




WiFiClient espClient;
PubSubClient client(espClient); 






const char *ssid = "TM0512";                 
const char *password = "05120512";           
const char *mqtt_server = "ia.ic.polyu.edu.hk"; 

const char *mqttTopic2_RX = "iot
const char *mqttTopic_RX = "iot

byte reconnect_count = 0;
int count = 0;
long int currentTime = 0;

char msg[200];
String ipAddress;
String macAddr;
String recMsg = "";

int Mode = 0;         
boolean keypress = 1;

int counters[13]={0};
bool state[13]={false};
bool page=false;
const char* warn;
bool pic1[64]={0,1,0,1,1,0,1,0,
               1,1,0,0,0,0,1,1,
               0,0,1,0,0,1,0,0,
               1,0,0,1,1,0,0,1,
               1,0,0,1,1,0,0,1,
               0,0,1,0,0,1,0,0,
               1,1,0,0,0,0,1,1,
               0,1,0,1,1,0,1,0};
bool pic2[64]={ 1,1,1,1,1,1,1,1,
1,1,1,1,0,1,1,1,
1,1,1,1,0,1,1,1,
1,1,1,1,1,1,1,1,
0,1,0,0,0,1,0,0,
0,1,0,0,1,1,0,0,
0,0,1,1,1,0,0,0,
0,0,0,0,0,0,0,0};
bool pic3[64]={ 
  1,1,1,1,1,1,1,1,
  1,1,1,1,0,1,1,1,
  1,1,1,1,0,1,1,1,
  1,1,1,1,1,1,1,1,
  0,1,0,0,0,0,0,0,
   0,1,0,0,0,0,0,0,
   0,1,0,0,1,1,0,0,
  0,0,1,1,1,0,0,0};
  bool pic4[64]={ 0,1,1,0,1,1,0,0,
  0,1,1,0,1,1,0,0,
  0,0,0,0,0,0,0,0,
  0,1,1,0,1,1,0,0,
  0,1,1,0,1,1,0,0,
  0,1,1,0,1,1,0,0,
  0,1,1,0,1,1,0,0,
  0,1,1,0,1,1,0,0 };

const char *Team = "A11";
const char *value = "Available";


StaticJsonDocument<50> Jsondata; 
StaticJsonDocument<200> jsonBuffer; 

#include <LedControl.h>



int DIN = D7; 
int CS = D4;   
int CLK = D5; 

LedControl lc = LedControl(DIN, CLK, CS, 1); 


byte ledMatrix[8]; 


void setPixel(int row, int col, boolean state) {
  if (state) {
    ledMatrix[row] |= (1 << (7 - col)); 
  } else {
    ledMatrix[row] &= ~(1 << (7 - col)); 
  }
}


void updateMatrix() {
  for (int i = 0; i < 8; i++) {
    lc.setRow(0, i, ledMatrix[i]);
  }
}


void clearMatrix() {
  for (int i = 0; i < 8; i++) {
    ledMatrix[i] = 0x00;
  }
  updateMatrix(); 
}
void drawInitialPixels() {
  clearMatrix(); 

  
  for (int i = 0; i < 8 && i < 11; i+=2) {
    setPixel(2, i, true);
    setPixel(4, i, true);
  }
  for (int i = 0; i < 6 && i < 11; i+=2) {
    setPixel(6, i, true);
  }
  
  updateMatrix(); 
}


void blinkPixel(int pixelNumber) {
  int row, col;

  
  if (pixelNumber <= 4) {
    row = 2;
    col = (pixelNumber - 1)*2;
  } else {
    if (pixelNumber<=8){
      row = 4;
      col = (pixelNumber - 5)*2;
    }else{
        row = 6;
        col = (pixelNumber - 9)*2;
      }
      
    }
    
    if (counters[pixelNumber-1]%40000==0){
      setPixel(row, col, false); 
      updateMatrix();            
    }else{
      if(counters[pixelNumber-1]%20000==0){
        setPixel(row, col, true);  
        updateMatrix();            
      }
    }
}




void setup_wifi() {
  WiFi.disconnect();
  delay(100);
  
  Serial.printf("\nConnecting to %s\n", ssid);
  WiFi.begin(ssid, password); 

  
  
  currentTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(green_light_pin, digitalRead(green_light_pin) ^ 1);
    if (millis() - currentTime > 30000) {
      ESP.restart();
    }
  }
  
  Serial.printf("\nWiFi connected\n");
  digitalWrite(green_light_pin, LOW);
  delay(2000);
  digitalWrite(green_light_pin, HIGH);

  
  ipAddress = WiFi.localIP().toString();
  Serial.printf("\nIP address: %s\n", ipAddress.c_str());
  macAddr = WiFi.macAddress();
  Serial.printf("MAC address: %s\n", macAddr.c_str());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("get message");
  recMsg = "";
  for (int i = 0; i < length; i++) {
    recMsg = recMsg + (char)payload[i];
  }

  DeserializationError error = deserializeJson(jsonBuffer, recMsg);

  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.c_str());
    return;
  }
  if (!page){
    
  if (jsonBuffer.containsKey("node_id")) {
      const char* nodeId = jsonBuffer["node_id"].as<const char*>();

      if (nodeId != NULL && nodeId[0] == 'A') {
        const char* numericPart = nodeId + 1;
        int nodeNumber = atoi(numericPart);

        
        if (nodeNumber < 10 && numericPart[0] == '0') {
          nodeNumber = atoi(numericPart + 1);
        }

        Serial.print("Node Number: ");
        Serial.println(nodeNumber);

        
        if (nodeNumber >= 1 && nodeNumber <= 11) {
          if (strcmp(topic, mqttTopic2_RX) == 0) {
            state[11]=true;
            page=true;
            warn = jsonBuffer["warn"].as<const char*>();
            Serial.print("warn: ");
            Serial.println(warn);
            warn_page(warn[0]);
            
            
          }else{
            state[nodeNumber-1]=true; 
          }
        } else {
          Serial.println("Node number is out of range (1-11).");
        }
      } else {
        Serial.println("Invalid node_id format. Should be Axx.");
      }
    } else {
      Serial.println("No 'node_id' key found in JSON.");
    }
  }
  
  
  
}

void reconnect() {

  
  while (!client.connected()) {
    Serial.printf("Attempting MQTT connection...");
    
    
    if (client.connect(macAddr.c_str())) {
      Serial.println("Connected");
      
      
      
      Serial.println(msg);
      client.subscribe(mqttTopic_RX); 
      client.subscribe(mqttTopic2_RX); 
      
      reconnect_count = 0;
    }
    else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      reconnect_count++;

      
      if (reconnect_count == 5) {
        ESP.restart(); 
      }

      
      delay(5000);
    }
  }
}

void setup() {
  pinMode(TRIG, INPUT_PULLUP);          
  pinMode(red_light_pin, OUTPUT);
  pinMode(green_light_pin, OUTPUT);
  pinMode(blue_light_pin, OUTPUT);

  digitalWrite(red_light_pin, HIGH);
  digitalWrite(green_light_pin, HIGH);
  digitalWrite(blue_light_pin, HIGH);

  Serial.begin(115200);                 
  Serial.println("System Start!");

  lc.shutdown(0, false);  
  lc.setIntensity(0, 8); 
  lc.clearDisplay(0);    

  
  drawInitialPixels();

  setup_wifi(); 
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback); 
}
void drawpic(bool pic[]){
  for(int i=0;i<8;i++){
    for(int j=0;j<8;j++){
      setPixel(i, j, pic[i*8+j]);  
    }
  }
  updateMatrix();
}
void warn_page(char sig){
  for (int i=0;i<7;i++){
    if (sig=='r'){
        drawpic(pic2);
        updateMatrix(); 
      }else{
        clearMatrix(); 
      }
      delay(1000);
        Serial.println(sig);
        switch (sig) { 
        case 'h': 
            drawpic(pic4);
            digitalWrite(green_light_pin, HIGH);
            digitalWrite(red_light_pin, LOW); 
            digitalWrite(blue_light_pin, HIGH);
            break;
        case 'c': 
            drawpic(pic1);
            digitalWrite(green_light_pin, HIGH);
            digitalWrite(red_light_pin, HIGH); 
            digitalWrite(blue_light_pin, LOW); 
            break;
        case 'r': 
            drawpic(pic3);
            digitalWrite(green_light_pin, HIGH);
            digitalWrite(red_light_pin, LOW); 
            digitalWrite(blue_light_pin, HIGH);
            break;
        default:
            printf("Unknown warning\n");
            break;
      
    }

        updateMatrix();  
        delay(1000);
  }
  clearMatrix();  
  drawInitialPixels();
  digitalWrite(green_light_pin, HIGH);
  digitalWrite(red_light_pin, HIGH); 
  digitalWrite(blue_light_pin, HIGH);
  page=false;
  state[11]=false;
                
}
void loop() {
for(int i=0;i<13;i++){
  if(state[i]){
    if(!page){
      blinkPixel(i+1);
    }
    counters[i]++;
    if(counters[i]>=360000){
      counters[i]=0;
      state[i]=false;
    }

  }
}
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); 
}