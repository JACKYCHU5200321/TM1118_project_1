#CHAN Chun Hei (24036095D)
#@reboot sleep 1 && python3 ~/Desktop/TEAM_A11_IOT.py
import paho.mqtt.client as mqtt
import time
import Adafruit_DHT
import Adafruit_ADS1x15
import math
import json
import datetime
import subprocess
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import threading
import socket
def check_wifi():
    try:
        socket.setdefaulttimeout(3)
        host="8.8.8.8"
        port=53
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.connect((host,port))
        return True
    except OSError:
        return False
while not check_wifi():
    time.sleep(1)
lcd = CharLCD('PCF8574', 0x27)


ID="A11"
LOC="W311D-Z2"
mqtt_broker = "ia.ic.polyu.edu.hk" # Broker
mqtt_client = mqtt.Client("iot-24036095D") # Create a Client Instance
mqtt_topic = "iot/sensor-A11"
mqtt_topic2 = "iot/alert-A11"

send_period=180

   

#IC/TM1118/TEAM_A11/PUB

    

            
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4

mqtt_port = 1883 # Default
mqtt_qos = 1 # Quality of Service = 1
mqtt_client.connect(mqtt_broker, mqtt_port) # Establish a connection to a broker
print("Connect to MQTT broker")
mqtt_client.subscribe(mqtt_topic, mqtt_qos) # topic=iot/student_ID, qos=1
mqtt_client.subscribe(mqtt_topic2, mqtt_qos) # topic=iot/student_ID, qos=1
adc = Adafruit_ADS1x15.ADS1115()
GAIN = 8
x=1500
adc_values=[]

last_message=""
last_topic=""
def on_disconnect(mqtt_client, userdata, rc):
    print("Disconnected with result code " + str(rc))
    # Attempt to reconnect
    while True:
        try:
            print(f"Reconnect")
            mqtt_client.reconnect()
            print(f"Reconnected,last_message:{last_message}")
            if last_message is not None:
                mqtt_client.publish(last_topic,last_message)
                print(f"Resent message: {last_message}")
            break
        except Exception as e:
            print(f"Reconnect failed: {e}")
            time.sleep(1)
mqtt_client.on_disconnect = on_disconnect

def get_adc():
    global adc_values
    adc_values = [0]*4
    inputs = []
    for i in range(4):
        adc_values[i] = adc.read_adc(i, gain=GAIN)
        
def get_snd():
    global x, GAIN,adc_values
    if adc_values[2]>0:
        dB = 20*math.log((adc_values[2]/500), 10)
        return int(dB+80)
    else:
        return 0
def get_light():
    global adc_values
    return int(adc_values[3]/32767*100)
    
# def mqtt_on_message(client, userdata, msg):
#     d_msg = str(msg.payload.decode("utf-8")) # Decode the messageprint("Received message on topic %s : %s" % (msg.topic, d_msg))
#     print("Received message on topic %s : %s" % (msg.topic, d_msg))
#     
# mqtt_client.on_message = mqtt_on_message
# mqtt_client.loop_start()
blink=False
GPIO.setmode(GPIO.BCM)
#output_channel = [18, 23, 24, 25, 8]
output_channel = [8]
GPIO.setup(output_channel, GPIO.OUT, initial=GPIO.LOW)
timer=0
def blinking():
    global blink
    while True:
        blink=not blink
        GPIO.output(output_channel, blink)
        time.sleep(1)
threading.Thread(target=blinking).start()

while True:
    if timer>10:
        try:
            print(f"Reconnect")
            mqtt_client.reconnect()
        except Exception as e:
            print(f"Reconnect failed: {e}")
    get_adc()
    if get_light()<=50 and get_snd()>50:
            iotDic={}
            iotDic["node_id"]=ID
            iotDic["warn"]="robber"
            iotDic["loc"]=LOC
            jsonData = json.dumps(iotDic) # Encode iotDic object to JSON
            mqtt_client.publish(mqtt_topic2, jsonData, mqtt_qos) # Publish a messageprint("Publishing message", jsonData ,"to topic", mqtt_topic)
            iotData = json.loads(jsonData)
            print(jsonData)
            last_message=jsonData
            last_topic=mqtt_topic2
            timer+=1
    #t = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")
    if timer==0 or timer>=send_period:
        timer=0
        get_adc()
        humidity, temp = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN) # Read the temperaturemqtt_client.publish(mqtt_topic, temperature, mqtt_qos) # Publish a messageprint("Publishing message %s to topic %s" % (temperature, mqtt_topic))
        iotDic={}
        iotDic["node_id"]=ID
        iotDic["loc"]=LOC
        iotDic["temp"]=str(temp)
        iotDic["hum"]=str(humidity)
        iotDic["light"]=str(get_light())
        iotDic["snd"]=str(get_snd())
        #iotDic["time"]=t
        jsonData = json.dumps(iotDic) # Encode iotDic object to JSON
        mqtt_client.publish(mqtt_topic, jsonData, mqtt_qos) # Publish a messageprint("Publishing message", jsonData ,"to topic", mqtt_topic)
        iotData = json.loads(jsonData)
        print(jsonData)
        last_message=jsonData
        last_topic=mqtt_topic
        if temp<10:#10 mean: cold
            iotDic={}
            iotDic["node_id"]=ID
            iotDic["warn"]="cold"
            iotDic["loc"]=LOC
            jsonData = json.dumps(iotDic) # Encode iotDic object to JSON
            mqtt_client.publish(mqtt_topic2, jsonData, mqtt_qos) # Publish a messageprint("Publishing message", jsonData ,"to topic", mqtt_topic)
            iotData = json.loads(jsonData)
            print(jsonData)
            last_message=jsonData
            last_topic=mqtt_topic2
        elif temp>=40:
            iotDic={}
            iotDic["node_id"]=ID
            iotDic["warn"]="hot"
            iotDic["loc"]=LOC
            jsonData = json.dumps(iotDic) # Encode iotDic object to JSON
            mqtt_client.publish(mqtt_topic2, jsonData, mqtt_qos) # Publish a messageprint("Publishing message", jsonData ,"to topic", mqtt_topic)
            iotData = json.loads(jsonData)
            print(jsonData)
            last_message=jsonData
            last_topic=mqtt_topic2
        
    lcd.cursor_pos = (0,0)
    lcd.write_string(f'TEAM A11 Node')
    lcd.cursor_pos = (1,0)
    lcd.write_string(f'Now Operating!')
    lcd.cursor_pos = (0,13)
    if timer>=100:
        lcd.write_string(f'{timer}')
    else:
        if timer>=10:
            lcd.write_string(f' {timer}')
        else:
            lcd.write_string(f'  {timer}')
    timer+=1
    time.sleep(1)
    jsonData=""
