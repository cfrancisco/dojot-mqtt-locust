# dojot-mqtt-locust
Load testing tool for dojot IoT platform using Locust.io and Paho MQTT client

Project based on mqtt-locust (https://github.com/concurrencylabs/mqtt-locust)

For more details, read this article: https://www.concurrencylabs.com/blog/hatch-a-swarm-of-things-using-locust-and-ec2/


# Installation

```shell
virtualenv mqtt-locust
pip install -r requirements.txt
```

# To run

```shell
 source bin/activate
 locust -f iot-publish.py -H localhost:1883
```

 or without GUI
```shell
 locust -f iot-publish.py -H iotmid-docker.cpqd.com.br:1883 --no-web -c 10 -r 10
```

 If you want run distribuited as master and slave model: 

Firsty, starts locust in master mode:
```shell
   locust -f iot-publish.py -H localhost:1883 --master
```
And then run on each slave machine:
```shell
   locust -f iot-publish.py --slave --master-host=localhost
```

# Dockerfile

Under development


# Changing System File Limitations

Basically you edit /etc/security/limits.conf and put in:

* hard nofile 500000

* soft nofile 500000

You may also need to modify /etc/sysctl.conf adding:

fs.file-max = 500000
sudo sysctl -p


To check uses: ulimit -a