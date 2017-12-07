import snowboydecoder
import sys
import wave
import paho.mqtt.client as mqtt
import struct
import StringIO
import json
import time
import collections
import pytoml
from piwho import recognition
import os.path

mqtt_client = mqtt.Client()
recog = recognition.SpeakerRecognizer()

dir = os.path.dirname(os.path.abspath(__file__))

clientList = []
allowedClientList = []
SENSITIVITY = 0.5
HOTWORD_SNOWBOY_FILE = dir + '/Hey_Janet.pmdl'
HOTWORD_ID = 'default'
MQTT_ADDRESS = '10.0.1.22'  #default just incase its not enabld in the toml file
MQTT_PORT = '1883'

path = '/Users/gregbail/XCodeProjects/GITHUB/snowboy/examples/Python/snips.toml'

if os.path.isfile(path):
    with open(path) as datafile:
        data = pytoml.load(datafile)
        if 'audio' in data['snips-hotword']:
            snipsClients = data['snips-hotword']['audio']
            for sc in snipsClients:
                allowedClientList.append(sc.split('@')[0])
        if 'hotword_id' in data['snips-hotword']:
            HOTWORD_ID = data['snips-hotword']['hotword_id']
        if 'sensitivity' in data['snips-hotword']:
            SENSITIVITY = data['snips-hotword']['sensitivity']
        if 'mqtt' in data['snips-common']:
            mqttstring = data['snips-common']['mqtt']
            MQTT_ADDRESS = mqttstring.split(':')[0]
            MQTT_PORT = mqttstring.split(':')[1]
else:
    #add something just incase it fails
    allowedClientList.append("zero")

detection = snowboydecoder.HotwordDetector(HOTWORD_SNOWBOY_FILE, sensitivity=SENSITIVITY)


#class to store audio after the hotword is spoken
class AudioBuffer(object):
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        self._buf.extend(data)

    def get(self):
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp

client_buffer = {}
client_recognition = {}
client_talking = {}
record = {}
for client in allowedClientList:
    client_buffer[client] = AudioBuffer(detection.detector.NumChannels() * detection.detector.SampleRate() * 20)
    client_recognition[client] =  AudioBuffer(detection.detector.NumChannels() * detection.detector.SampleRate() * 2)
    client_talking[client] = False
    record[client] = False

def on_connect(client, userdata, flags, rc):
    for allowedClient in allowedClientList:
        mqtt_client.subscribe('hermes/audioServer/{}/audioFrame'.format(allowedClient))
    mqtt_client.subscribe('hermes/hotword/toggleOff')
    mqtt_client.subscribe('hermes/hotword/toggleOn')

def on_message(client, userdata, msg):
    if msg.topic == 'hermes/hotword/toggleOff':
        msgJSON = json.loads(msg.payload)
        if msgJSON['siteId'] not in clientList:
            clientList.append(msgJSON['siteId'])
    elif msg.topic == 'hermes/hotword/toggleOn':
        msgJSON = json.loads(msg.payload)
        if client_talking[msgJSON['siteId']] == True:
                #timeout occured so clear the buffer
                data = client_buffer[msgJSON['siteId']].get()
        clientList.remove(msgJSON['siteId'])
    else:
        siteId = msg.topic.split('/')[2]
        if siteId not in clientList:
            data = msg.payload[44:struct.unpack('<L', msg.payload[4:8])[0]]
            client_recognition[siteId].extend(data)

            ans = detection.detector.RunDetection(data)

            if ans == 1:
                record[siteId] = True

                #inform that the hotword has been detected
                client.publish('hermes/hotword/{}/detected'.format(HOTWORD_ID), payload="{\"siteId\":\"" + siteId + "\"}", qos=0)

                waveFile = wave.open( siteId + '_id.wav', 'wb')
                waveFile.setnchannels(1)
                waveFile.setsampwidth(2)
                waveFile.setframerate(16000)
                waveFile.writeframes(client_recognition[siteId].get()) 
                waveFile.close()
                speaker = recog.identify_speaker(siteId + '_id.wav')[0]

                action = "{\"type\":\"action\",\"text\":null,\"canBeEnqueued\":false,\"intentFilter\":null}"
                jsonString = "{\"siteId\":\"" + siteId + "\",\"init\":" + action + ",\"customData\":\"" + speaker + "\"}"

                client.publish('hermes/dialogueManager/startSession', payload=jsonString, qos=0)

                client_buffer[siteId].extend(data)
                clientList.append(siteId)
                
        elif record[siteId] == True:
            #i want to capture what is said after the hotword as a wave
            data = msg.payload[44:struct.unpack('<L', msg.payload[4:8])[0]]
            client_buffer[siteId].extend(data)
            ans = detection.detector.RunDetection(data)
            if ans == 0:
                #adding the data here misses the first 0.1 sec of the speaking audio and it sounds off
                #saying "what is the...." the audio is "ot is the..".. the first word lacks the whole sound
                #client_buffer[siteId].extend(data)
                client_talking[siteId] = True
            elif ans == -2 and client_talking[siteId] == True:
                client_talking[siteId] = False
                record[siteId] = False
                data = client_buffer[siteId].get()
                #save wave file
                waveFile = wave.open( siteId + '.wav', 'wb')
                waveFile.setnchannels(1)
                waveFile.setsampwidth(2)
                waveFile.setframerate(16000)
                waveFile.writeframes(data) 
                waveFile.close()
                


if __name__ == '__main__':
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_ADDRESS, int(MQTT_PORT))
    mqtt_client.loop_forever()