# dojot-mqtt-locust
Load test for dojot IoT platform using Locust.io and Paho MQTT client

Project based on mqtt-locust (https://github.com/concurrencylabs/mqtt-locust)

For more details, read this article: https://www.concurrencylabs.com/blog/hatch-a-swarm-of-things-using-locust-and-ec2/


#installation

virtualenv mqtt-locust
pip install locustio pyzmq paho-mqtt


# to run
 source bin/activate
 locust -f iot-publish.py -H localhost:1883



#Changing System File Limitations

Basically you edit /etc/security/limits.conf and put in:

* hard nofile 500000

* soft nofile 500000

You may also need to modify /etc/sysctl.conf and put in:

fs.file-max = 2097152
sudo run sysctl -p



