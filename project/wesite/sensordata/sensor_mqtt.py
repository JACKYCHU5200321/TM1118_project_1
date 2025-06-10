import paho.mqtt.client as mqtt
from .models import SensorRecord
import json

ID="A11"
mqtt_broker = "ia.ic.polyu.edu.hk"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/sensor-A"


def try_loadJSON(msg):
    try:
        jsonData = json.loads(msg)
        if isinstance(jsonData, dict):
            return jsonData    
        return None
    except ValueError as e:
        return None
        
def try_getJSON(json, attr):
    try:
        val = json[attr]
        return val
    except KeyError as e:
        return None

def try_exec_for(json, attr, f):
    if val := try_getJSON(json, attr):
        return f(val)
    return None

accepted_node_ids = ["A11"]

def mqtt_on_message(client, userdata, msg):
    d_msg = str(msg.payload.decode("utf-8"))

    json = try_loadJSON(d_msg)
    if json:
        # msg_id = try_getJSON(json, "node_id")
        # msg_loc = try_getJSON(json, "loc")
        # msg_temp = try_getJSON(json, "temp")
        # msg_hum = try_getJSON(json, "hum")
        # msg_light = try_getJSON(json, "light")
        # msg_snd = try_getJSON(json, "snd")

        msg_id, msg_loc, msg_temp, msg_hum, msg_light, msg_snd = map(lambda x: try_getJSON(json, x), ["node_id", "loc", "temp", "hum", "light", "snd"])
        if all([msg_id, msg_loc, msg_temp, msg_hum, msg_light, msg_snd]):
            print("Received json on topic %s : %s" % (msg.topic, d_msg))
            # if msg_id in accepted_node_ids:
            print("Accpeted Node ID: %s" % msg_id)
            p = SensorRecord(node_id=msg_id, loc=msg_loc, temp=msg_temp, hum=msg_hum, light=msg_light, snd=msg_snd)
            p.save()
            # else:
                # print("Rejected Node ID: %s" % msg_id)
        else:
            print("Received invalid-json on topic %s : %s" % (msg.topic, d_msg))
    else:
        print("Received non-json on topic %s : %s" % (msg.topic, d_msg))

    # iotData = json.loads(d_msg)
    # if iotData["node_id"] == ID:
        # print("Received message on topic %s : %s" % (msg.topic, iotData))
        # p = SensorRecord(node_id=iotData["node_id"], loc=iotData["loc"], temp=iotData["temp"], hum=iotData["hum"], light=iotData["light"], snd=iotData["snd"], date_created=iotData["time"])
        # p.save()

mqtt_client = mqtt.Client("django-sensor-A")
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker, mqtt_port)
print("Connect to MQTT broker")
mqtt_client.subscribe(mqtt_topic, mqtt_qos)

mqtt_client.loop_start()