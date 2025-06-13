#define MQTT_MAX_PACKET_SIZE 256
#include <WiFi.h>               // Wifi driver
#include <PubSubClient.h>       // MQTT server library
#include <ArduinoJson.h>        // JSON library
#include <string>
#include <NTPClient.h>
//#include <M5StickC.h>
//#include <M5Unified.h>
#include <M5StickCPlus2.h>
#include <DFRobot_DHT11.h>      // DHT11 library
#include <math.h>
#include "bitmap.h"
#define DATA 0                  // DHT11 data pin
#define ID 9
#define LED 26
//define
  // DHT11
  DFRobot_DHT11 dht;

  // Operating parameters
  const float pi=3.14159;
  float self_temp,self_hum;
  char node_id[10]; // Buffer for node_id (e.g., "A08")
  char loc[20];     // Buffer for location (e.g., "W311-H2")
  float temp =25;       // Temperature (e.g., 31.0)
  float hum =50;        // Humidity (e.g., 42.0)
  bool first_receive=false;
  int light;        // Light level (e.g., 5)
  int snd;          // Sound level (e.g., -80)
    int year ;
    int short_year;
    int month;
    int day ;
    int hour ;
    int minute;
    int second;
  // MQTT and WiFi set-up
  WiFiClient espClient;
  PubSubClient client(espClient);
  //Neotimer mytimer(900000); // Set timer interrupt to 15min

  // NTP Client setup
  WiFiUDP ntpUDP;
  NTPClient timeClient(ntpUDP, "pool.ntp.org", 8*3600, 60000); // Update every 60 seconds

  // Key debounce set-up
  //ButtonDebounce trigger(TRIG, 100);//IO debouncing
  //ButtonDebounce function_key(FUNC_KEY, 100); //IO debouncing

  const char *ssid = "TM0512";              // Your SSID             
  const char *password = "05120512";             // Your Wifi password
  const char *mqtt_server = "ia.ic.polyu.edu.hk"; // MQTT server name
  //const char *mqtt_server = "192.168.0.170";
  char *mqttTopic = "iot/sensor-A";
  String doc ="";
  byte reconnect_count = 0;
  long currentTime = 0;
  const char* weekday;
  char msg[100];
  String recMsg;
  String ipAddress;
  String macAddr;

  StaticJsonDocument<500> Jsondata; // Create a JSON document of 200 characters max
float getBatteryLevel() {
  float vbat = StickCP2.Power.getBatteryVoltage();
  float percentage = (vbat - 3.0) / (4.2 - 3.0) * 100.0;
  if (percentage > 100.0) percentage = 100.0;
  if (percentage < 0.0) percentage = 0.0;
  return (percentage+1)/25;
}
void setup_wifi() {
  byte count = 0;
  
  WiFi.disconnect();
  delay(100);
  // We start by connecting to a WiFi network
  Serial.printf("\nConnecting to %s\n", ssid);
  WiFi.begin(ssid, password); // start the Wifi connection with defined SSID and PW

  // Indicate "......" during connecting
  // Restart if WiFi cannot be connected for 30sec
  currentTime = millis();
  M5.Lcd.setCursor(0,0);
  M5.Lcd.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    M5.Lcd.print(".");
    count++;
    if (count == 6) {
      count = 0;
      M5.Lcd.setCursor(0,0);
      M5.Lcd.print("Connecting       "); //clear the dots
      M5.Lcd.setCursor(0,0);
    }
      
    if (millis()-currentTime > 30000){
      ESP.restart();
    }
  }
  // Show "WiFi connected" once linked and light up LED1
  Serial.printf("\nWiFi connected\n");
  // Show IP address and MAC address
  ipAddress=WiFi.localIP().toString();
  Serial.printf("\nIP address: %s\n", ipAddress.c_str());
  macAddr=WiFi.macAddress();
  Serial.printf("MAC address: %s\n", macAddr.c_str());
  
  //Show in the small TFT
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0,0);
  M5.Lcd.print("WiFi connected!");
  delay(3000);
  M5.Lcd.fillScreen(BLACK);
}

// Routine to receive message from MQTT server
void callback(char* topic, byte* payload, unsigned int length) {
// Clear previous message
  recMsg = "";

  // Build recMsg from payload
  for (unsigned int i = 0; i < length; i++) {
    recMsg += (char)payload[i];
  }

  // Debug: Print topic and recMsg
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("], Length: ");
  Serial.println(length);
  Serial.print("recMsg: [");
  Serial.print(recMsg);
  Serial.println("]");

  // Check if recMsg is empty
  if (recMsg.length() == 0) {
    Serial.println("Error: recMsg is empty");
    return;
  }

  // Parse JSON
  DynamicJsonDocument doc(200);
  DeserializationError error = deserializeJson(doc, recMsg);
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Check node_id
  const char* target_node_id = "A08"; // Replace with your desired node_id
  const char* received_node_id = doc["node_id"].as<const char*>();
  if (strcmp(received_node_id, target_node_id) != 0) {
    Serial.print("Ignoring message: node_id ");
    Serial.print(received_node_id);
    Serial.println(" does not match target ");
    return;
  }

  // Extract JSON values for matching node_id
  strncpy(node_id, received_node_id, sizeof(node_id));
  node_id[sizeof(node_id) - 1] = '\0';
  strncpy(loc, doc["loc"].as<const char*>(), sizeof(loc));
  loc[sizeof(loc) - 1] = '\0';
  temp = doc["temp"].as<float>();
  hum = doc["hum"].as<float>();
  light = doc["light"].as<int>();
  snd = doc["snd"].as<int>();

  // Format and print output
  char output[100];
  sprintf(output, "Node: %s, Loc: %s, Temp: %.1f, Hum: %.1f, Light: %d, Snd: %d",
          node_id, loc, temp, hum, light, snd);
  Serial.println(output);

  first_receive=true;
};
// Reconnect mechanism for MQTT Server
void reconnect() {
  // Loop until we're reconnected
  
  while (!client.connected()) {
    Serial.printf("Attempting MQTT connection...");
    // Attempt to connect
    //if (client.connect("ESP32Client")) {
    if (client.connect(macAddr.c_str())) {
      Serial.println("Connected");
      // Once connected, publish an announcement...
      snprintf(msg, 75, "IoT System (%s) is READY", ipAddress.c_str());
      client.subscribe(mqttTopic);
      delay(1000);
      client.publish(mqttTopic, msg);
      reconnect_count = 0;
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      reconnect_count++;
      
      //reconnect wifi by restart if retrial up to 5 times
      if (reconnect_count == 5){
        ESP.restart();//reset if not connected to server 
      }
        
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void get_time(){
  unsigned long epochTime = timeClient.getEpochTime();
  struct tm* timeInfo;
  //char dateStr[20]=""; // Buffer for YYYY-MM-DD
  time_t rawTime = epochTime;
    timeInfo = localtime(&rawTime);
      //strftime(dateStr, sizeof(dateStr), "%Y-%m-%d %H:%M:%S", timeInfo);
        year = timeInfo->tm_year + 1900; // tm_year is years since 1900
        short_year = year % 100;        // Last two digits of year (YY)
        month = timeInfo->tm_mon + 1;    // tm_mon is 0-11, so add 1
        day = timeInfo->tm_mday;         // Day of the month (1-31)
        hour = timeInfo->tm_hour;        // Hours (0-23)
        minute = timeInfo->tm_min;       // Minutes (0-59)
        second = timeInfo->tm_sec;       // Seconds (0-59)
  const char* weekdays[] = {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"};
  weekday = weekdays[timeInfo->tm_wday];
}
void mqtt_pub(){
  char pub_data[256]=""; // Buffer to hold the serialized JSON
  // Get epoch time and format the date
  // For Humidity  
  Serial.print("Humidity : ");  
  Serial.print(self_hum);
  Serial.println("%");  
  // For Temprature   
  Serial.print("Temperature : ");  
  Serial.print(self_temp);  
  Serial.println("degC ");  


  Jsondata["node_id"] = "M5Stick-C_Plus2";
  Jsondata["loc"] = "W204C";
  Jsondata["temp"] = self_temp;
  Jsondata["hum"] = self_hum; 
  //Jsondata["time"] = dateStr;

  serializeJson(Jsondata, pub_data);

  // Publish the JSON string via MQTT
  client.publish(mqttTopic, pub_data);
  Jsondata.clear();
}
void Buzzer_Icon(int x,int y,int size,int colour){//Start at mid left
   M5.Lcd.fillTriangle(x,y,x+size,y-size,x+size,y+size,colour);//3 point form Black Triangle
   M5.Lcd.fillRect(x,y-size/2,size/2,size,colour);
   M5.Lcd.drawLine(x+size/2-1,y+size/2-1,x+size/2-1,y-size/2,0xffff);
}

void Water_Droplets_Icon(int x,int y,int radius,int colour){//Start at center
   M5.Lcd.fillCircle(x , y, radius, colour);
   M5.Lcd.fillRect(x-radius,y-radius*2.5,2*radius+1,2.5*radius,0x94b1);//gray
   M5.Lcd.fillTriangle(x-radius,y,x+radius,y,x,y-radius*2.5,colour);
   

}

void Battery_Icon(int x , int y , int size ,int level, int colour,int rot){//Start at top left
  M5.Lcd.setRotation(rot);
  int height=1.8*size;
  M5.Lcd.fillRect(x,y,size,size*1.8,colour);
  M5.Lcd.fillRect(x+(size+1)/3,y-size/4,(size+1)/3,size/4,colour);
  for (int i=1;i<=level;i++){
    if (level==1){
    colour=0xda25;}//red
    else colour=0x2644;//green
    if (i==1){
      height=height-2-((size*1.8-7)/4);
    }
    else height = height-1-((size*1.8-7)/4);
    M5.Lcd.fillRect(x+2,y+height,size-4,((size*1.8-7)/4),colour);
  }
}
void Temperature_Icon(int x , int y , int radius, int temp, int colour){//Start at center of circle
   M5.Lcd.fillRect(x-0.5*radius,y-radius*7,radius,7*radius,0xffff);
   M5.Lcd.fillCircle(x , y, radius, 0xffff);
   M5.Lcd.fillCircle(x , y, radius-2, colour);
   M5.Lcd.fillRect(x-0.2*radius,y-radius*7,0.7*radius,7*radius,0x94b1);//gray
   M5.Lcd.fillRect(x-0.2*radius,y-temp,0.7*radius,temp,colour);
}
void Clock_Icon(int x , int y ,int hour , int min){//start at top left square box
  int center_xh,center_yh,center_xm,center_ym;
   M5.Lcd.drawBitmap(x, y, 80, 80, epd_bitmap_clock);
   center_xm = x+40-int((int(min+1))%60/30);
   center_xh = x+40-int((int(hour+1))%12/6);
   if (min<=15 or min>=45){
   center_ym=y+40;}
   else {center_ym=y+41;}  
   if (hour<=3 or hour>=9){
   center_yh=y+40;}
   else {center_yh=y+41;}
   M5.Lcd.drawLine(center_xm,center_ym,center_xm+25*sin(min*6*pi/180),center_ym-25*cos(min*6*pi/180),0xf800);//min line
   M5.Lcd.drawLine(center_xh,center_yh,center_xh+18*sin((hour*30+min/2)*pi/180),center_yh-18*cos((hour*30+min/2)*pi/180),0x2979);//min line
  }

void UI_1(){
  //pinMode(LED, OUTPUT);
  //digitalWrite(LED, LOW);

  Clock_Icon(10,30,hour%12,minute);
  //M5.Lcd.drawRect(10, 5, 52, 20, 0xffff);//x,y,w,h,white time block
  M5.Lcd.setTextSize(1.6);
  M5.Lcd.setCursor(11, 6);
  M5.Lcd.setTextColor(0xffff, 0x0000);//text,background
  int h1= hour/10;
  int h2= hour%10;
  int m1=minute/10;
  int m2=minute%10;
  String timer= String(h1)+String(h2)+":"+String(m1)+String(m2);
  M5.Lcd.println(timer);
  
  //M5.Lcd.drawRect(10, 115, 80, 20, 0xffff);// date text field
  M5.Lcd.setTextSize(1.2);
  M5.Lcd.setCursor(17, 116);
  M5.Lcd.println("2025-06-11");
  M5.Lcd.setCursor(17, 126);
  M5.Lcd.print(weekday);
  M5.Lcd.print(" ");
  M5.Lcd.print(node_id);
  // battery block//M5.Lcd.drawRect(100, 5, 27, 15, 0xffff);
  Battery_Icon(5,7,15,getBatteryLevel(),0xffff,1);
  M5.Lcd.setRotation(0);
  
  //M5.Lcd.drawRect(101, 115, 24, 42, 0xffff);//hum block
  //M5.Lcd.drawRect(97, 162, 32, 20, 0xffff);//hum data
   M5.Lcd.fillRect(97, 115, 32, 162-115+20, 0x94b1);
   M5.Lcd.drawRect(97, 115, 32, 162-115+20, 0xffff);
  Water_Droplets_Icon(101+24/2,115+42-10-1,10,0x42da);
  M5.Lcd.setTextColor(0x0000, 0x94b1);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setCursor(98, 165);
   if (first_receive){
  M5.Lcd.printf("%4.1f", hum);
  M5.Lcd.print("%");}
  else{M5.Lcd.print("load");}

  //M5.Lcd.drawRect(105, 30, 16, 56, 0xffff);//temp block
  //M5.Lcd.drawRect(97, 90, 32, 20, 0xffff);//temp data
   M5.Lcd.fillRect(97, 30, 32, 90-30+20, 0x94b1);
   M5.Lcd.drawRect(97, 30, 32, 90-30+20, 0xffff);
  Temperature_Icon(105+16/2,30+56-6-1,6,int(temp),0xf1a0);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setCursor(98, 91);
  if (first_receive){
  M5.Lcd.printf("%4.1f", temp);
  M5.Lcd.print("C");}
  else{M5.Lcd.print("load");}
  

  M5.Lcd.drawRect(15, 140, 70, 70, 0xffff);// emoji block
  M5.Lcd.drawRect(10, 220, 120, 15, 0xffff);//nav bar 
  
  M5.Lcd.setTextColor(0xffff, 0x0000);

}
void setup() {
  Serial.begin(115200); 
  Serial.println("System Start!");  
  pinMode(LED, OUTPUT);
  digitalWrite(LED, LOW);
  
  M5.begin();
  

  setup_wifi();
  timeClient.begin();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  //Initalize Json message
  Jsondata["node_id"] = "A11";
  Jsondata["temp"] = self_temp;
  Jsondata["hum"] = self_hum;
  //Jsondata["time"] = "";
  M5.Lcd.setRotation(0);
  M5.Lcd.fillScreen(0x0000);//Gray0x94b1
  UI_1();
}
void loop() {
  if (!client.connected()){
    reconnect();
   }
  client.loop();
  
  timeClient.update();
  
  get_time();
  char dateTime[30];
  //sprintf(dateTime, "%04d-%02d-%02d %s %02d:%02d:%02d", 
  //        year, month, day, weekday, hour, minute, second);
  //Serial.println(dateTime); // Prints: 2025-06-11 Wed 15:14:00

  // DHT11
  dht.read(DATA);
  self_hum = dht.humidity;  
  self_temp = dht.temperature; // in Celcius  
  UI_1();
  
  digitalWrite(LED,digitalRead(LED)^1);
  delay(2000);
}
