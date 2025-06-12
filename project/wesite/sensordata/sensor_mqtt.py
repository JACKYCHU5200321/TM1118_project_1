import paho.mqtt.client as mqtt
from .models import SensorRecord, Alert
import json

# ID="A11"
mqtt_broker = "ia.ic.polyu.edu.hk"
# mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
mqtt_qos = 1
mqtt_topic = "iot/sensor-A"
mqtt_topic_alert = "iot/alert-A11"


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

# accepted_node_ids = ["A11"]

def mqtt_on_message(client, userdata, msg):
    d_msg = str(msg.payload.decode("utf-8"))
    json = try_loadJSON(d_msg)
    if json:

        warning = try_getJSON(json, 'warn')
        if warning:
            print("Received alert on topic %s : %s" % (msg.topic, d_msg))
            node_id = try_getJSON(json, 'node_id')
            loc = try_getJSON(json, 'loc')
            p = Alert(type_alert=warning, loc=loc, node_id=node_id)
            p.save()
            return

        msg_id, msg_loc, msg_temp, msg_hum, msg_light, msg_snd = map(lambda x: try_getJSON(json, x), ["node_id", "loc", "temp", "hum", "light", "snd"])
        if all([msg_id, msg_loc, msg_temp, msg_hum, msg_light, msg_snd]):
            print("Received record on topic %s : %s" % (msg.topic, d_msg))
            p = SensorRecord(node_id=msg_id, loc=msg_loc, temp=msg_temp, hum=msg_hum, light=msg_light, snd=msg_snd)
            p.save()
        else:
            print("Received invalid-json on topic %s : %s" % (msg.topic, d_msg))
    else:
        print("Received non-json on topic %s : %s" % (msg.topic, d_msg))


mqtt_client = mqtt.Client("django-sensor-Group12")
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect(mqtt_broker, mqtt_port)
print("Connect to MQTT broker")
mqtt_client.subscribe(mqtt_topic, mqtt_qos)
mqtt_client.subscribe(mqtt_topic_alert, mqtt_qos)

mqtt_client.loop_start()