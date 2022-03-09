#Robert Dilks Final Project Raspberry Pi Client
#This program accepts messages from AWS IoT in the form of Shadow Documents. These documents are in a JSON
# based format and are compared with the current state of the LED bulb being powered by a Raspberry Pi 4 
# via the GPIO pins. 
#KNOWN BUGS: Connection times out without being prompted



import paho.mqtt.client as mqtt
import wiringpi
import ssl, time, sys, requests
import subprocess, json, re
# MQTT Setup
#AWS Endpoint
mqttHost = "a3rcwrcspths01-ats.iot.us-east-2.amazonaws.com"
# CA Root Certificate File Path
caRootFile = "AmazonRootCA1.pem"
# AWS IoT Thing Name
thingName = "RaspPi"
# AWS IoT Thing Certificate File Path
thingCertFile = "246f0a9fb2-certificate.pem.crt"
# AWS IoT Thing Private Key File Path
thingPrivateKey = "246f0a9fb2-private.pem.key"
mqttPort = 8883
mqttKeepalive = 6000
#Defining all of the topics needed on the Raspberry Pi side as well as documents
shadowUpdate = "$aws/things/" + thingName + "/shadow/update"
shadowUpdateAccepted = "$aws/things/" + thingName + "/shadow/update/accepted"
getShadow = "$aws/things/" + thingName + "/shadow/get"
getShadowAccepted = "$aws/things/" + thingName + "/shadow/get/accepted"
shadowUpdateRejected = "$aws/things/" + thingName + "/shadow/update/rejected"
getShadowRejected = "$aws/things/" + thingName + "/shadow/get/rejected"
shadowUpdateDelta = "$aws/things/" + thingName + "/shadow/update/delta"
OnJSON = "/JSON/shadowOn.json"
OffJSON = "/JSON/shadowOff.json"

with open (OnJSON,'r') as j:
	LED_ON = str(j.read())

with open (OffJSON,'r') as k:
	LED_OFF = str(k.read())

# Sets Up the GPIO pins using the wiringpi import. 
# Grants the program root permissions as is required to use the GPIO pins.
def setup(): 
    returncode = subprocess.call(["usr/bin/sudo", "usr/bin/id"])
    wiringpi.wiringPiSetup()    # use PHYSICAL GPIO Numbering
    wiringpi.pinMode(0, 1)      # set the LED Pin to OUTPUT mode
    wiringpi.digitalWrite(0, 0) # make LED Pin output 0 (OFF), 1 is ON 
    print("Using pin 14")

mqttc = mqtt.Client()

#LED Control Function that changes the state of the bulb if the shadow document has changed
def LED_Status_Change(Shadow_State_Doc, Type):
	shadowState = json.loads(Shadow_State_Doc)
	if Type == "DELTA":
		ledStatus = shadowState['state']['LED']
	elif Type == "GET_REQ":
		ledStatus = shadowState['state']['desired']['LED']
	print ("Desired LED Status: " + ledStatus) 
	
	if ledStatus == "ON":
		# Turning on the LED
		wiringpi.digitalWrite(0, 1)
		#Report LED ON back to the shadow
		mqttc.publish(shadowUpdate,LED_ON.encode("utf-8"),qos=1) 
	elif ledStatus == "OFF":
		# Turning off the LED
		wiringpi.digitalWrite(0, 0)
		# Report LED OFF back to Shadow 
		mqttc.publish(shadowUpdate,LED_OFF.encode("utf-8"),qos=1)

def on_connect(mosq, obj, rc, properies=None):
	print ("Connected to AWS IoT...")
	# Subscribe to Update Topic
	mqttc.subscribe(shadowUpdateDelta, 1)
	# Subscribe to Update Accepted and Update Rejected Topics
	mqttc.subscribe(shadowUpdateAccepted, 1)
	mqttc.subscribe(getShadowRejected, 1)	
	# Subscribe to Get Accepted and Get Rejected Topics
	mqttc.subscribe(getShadowAccepted, 1)
	mqttc.subscribe(getShadowRejected, 1)
#Parses messages sent from AWS IoT via the shadow document located inside the subscription topics 
def on_message(mosq, obj, msg, properties=None):
	if str(msg.topic) == shadowUpdateDelta:
		shadowDeltaState = (msg.payload).decode("UTF-8")
		LED_Status_Change(shadowDeltaState, "DELTA")
	elif str(msg.topic) == getShadowAccepted:
		Shadow_State_Doc = (msg.payload).decode("UTF-8")
		LED_Status_Change(Shadow_State_Doc, "GET_REQ")
	elif str(msg.topic) == getShadowRejected:
		getShadowError = (msg.payload).decode("UTF-8")
	elif str(msg.topic) == shadowUpdateAccepted:
		print ("\nLED Status Change Updated SUCCESSFULLY in Shadow...")
	elif str(msg.topic) == getShadowRejected:
		shadowError = (msg.payload).decode("UTF-8")
		print ("\n---ERROR--- Failed to Update the Shadow...\nError Response: " + shadowError)
	else:
		print ("AWS Response Topic: " + str(msg.topic))
		print ("QoS: " + str(msg.qos))
		print ("Payload: " + str(msg.payload))

#Gets the current shadow upon subscription
def on_subscribe(mosq, obj, mid, granted_qos):
	if mid == 3:
		mqttc.publish(getShadow,"",qos=1)
#indicates if the program disconnected from AWS IoT
def on_disconnect(client, userdata, rc, properties=None):
    if rc != 0:
        print ("Diconnected from AWS IoT. Trying to auto-reconnect...")

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect


# Configure TLS Set
mqttc.tls_set(caRootFile, certfile=thingCertFile, keyfile=thingPrivateKey, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(mqttHost, mqttPort, mqttKeepalive)	

setup()

# Continue monitoring the incoming messages for subscribed topic
mqttc.loop_forever()

