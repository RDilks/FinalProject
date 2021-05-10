#Robert Dilks Final Project Web Client
#Web Client used to interact with the IoT device/program used to turn on an off an LED light via GPIO pins on 
#Raspberry Pi 4. Sends out messages to AWS IoT that updates the Things shadow, which is used to update its state.
#KNOWN BUGS: Times out after being active for a while




from flask import Flask, redirect, url_for, render_template, request
import paho.mqtt.client as mqtt
import os
import socket
import ssl


app = Flask(__name__)
#Beginning of Application, defining all of the certifications, addresses, ports, and files used
awshost = "a3rcwrcspths01-ats.iot.us-east-2.amazonaws.com"
awsport = 8883
clientId = "RaspPi"
thingName = "RaspPi"
caPath = "AmazonRootCA1.pem.crt"
certPath = "246f0a9fb2-certificate.pem.crt"
keyPath = "246f0a9fb2-private.pem.key"
OnJSON = "shadowOn.json"
OffJSON = "shadowOff.json"
with open (OnJSON, 'r') as j:
	dOnJSON = str(j.read())
with open (OffJSON, 'r') as k:
	dOffJSON = str(k.read())
topicUpdate = '$aws/things/RaspPi/shadow/update'

#Connects the Website to AWS IoT using MQTT
def on_connect(client, userdata, rc):
    client.subscribe(topicUpdate)
    print("Connecting to AWS")

#Send out the updated shadow to tell the IoT device to turn on the light
def turnOn():
    client.publish(topicUpdate, dOnJSON.encode('UTF-8'), qos=1)
    print("Light is now on")

#Send out the updated shadow to tell the IoT device to turn off the light
def turnOff():
    client.publish(topicUpdate, dOffJSON.encode('UTF-8'), qos=1)
    print("Light is now off")


#Builds the Websit from a html document and handles interaction with the site
@app.route("/", methods= ["POST", "GET"])
def home():

    if request.method == "POST":
        if request.form["submit"] =="On":
            turnOn()
        elif request.form["submit"] == "Off":
            turnOff()
        return render_template("backup.html")
    return render_template("backup.html")


#Connects the program to the cloud via MQTT then launches the website
if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    client.connect(awshost, awsport, keepalive=6000)
    client.loop_forever

    app.run(host="0.0.0.0", port=5000, use_reloader=False)

