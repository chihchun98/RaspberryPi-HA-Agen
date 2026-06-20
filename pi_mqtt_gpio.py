import paho.mqtt.client as mqtt
import json
import time
import RPi.GPIO as GPIO

# Configuration
BROKER = "192.168.0.254"
PORT = 1883
PINS = [14, 15, 18, 23, 24]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT with result code {rc}")
    
    # Publish HA Discovery payloads
    for pin in PINS:
        config_topic = f"homeassistant/switch/pi_gpio_{pin}/config"
        payload = {
            "name": f"Pi GPIO {pin}",
            "unique_id": f"pi_gpio_{pin}",
            "command_topic": f"rpi_agent/gpio/{pin}/set",
            "state_topic": f"rpi_agent/gpio/{pin}/state",
            "payload_on": "ON",
            "payload_off": "OFF",
            "icon": "mdi:chip",
            "device": {
                "identifiers": ["pi_gpio_controller"],
                "name": "Raspberry Pi GPIO Controller",
                "manufacturer": "Custom"
            }
        }
        client.publish(config_topic, json.dumps(payload), retain=True)
        # Publish initial state
        client.publish(f"rpi_agent/gpio/{pin}/state", "OFF", retain=True)
        # Subscribe to command topic
        client.subscribe(f"rpi_agent/gpio/{pin}/set")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    print(f"Received {payload} on {topic}")
    
    # topic format: rpi_agent/gpio/{pin}/set
    parts = topic.split('/')
    if len(parts) == 4 and parts[-1] == "set":
        try:
            pin = int(parts[2])
            if pin in PINS:
                if payload == "ON":
                    GPIO.output(pin, GPIO.HIGH)
                    client.publish(f"rpi_agent/gpio/{pin}/state", "ON", retain=True)
                elif payload == "OFF":
                    GPIO.output(pin, GPIO.LOW)
                    client.publish(f"rpi_agent/gpio/{pin}/state", "OFF", retain=True)
        except Exception as e:
            print(f"Error handling message: {e}")

# paho-mqtt v2 requires CallbackAPIVersion
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(BROKER, PORT, 60)
        break
    except Exception as e:
        print(f"Connection failed: {e}. Retrying in 5 seconds...")
        time.sleep(5)

client.loop_forever()
