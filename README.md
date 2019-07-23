# dojot-mqtt-locust
dojot-mqtt-locust is a Load testing tool for dojot IoT platform using Locust.io and Paho MQTT client

Project based on mqtt-locust (https://github.com/concurrencylabs/mqtt-locust)

For more details, read this article: https://www.concurrencylabs.com/blog/hatch-a-swarm-of-things-using-locust-and-ec2/


# Installation

```shell
virtualenv dojot-mqtt-locust
pip install -r requirements.txt
```

# To run

```shell
 source bin/activate
 locust -f iot-publish.py -H localhost:1883
```
or
```
 python3 -m locust.main  -f iot-publish.py -H localhost:1883
```


 or without GUI
```shell
 locust -f iot-publish.py -H iotmid-docker.cpqd.com.br:1883 --no-web -c 10 -r 10
```

 If you want run distribuited as master and slave schema: 

Firsty, starts locust in master mode:
```shell
   locust -f iot-publish.py -H localhost:1883 --master
```
And then run on each slave machine:
```shell
   locust -f iot-publish.py --slave --master-host=localhost
```

# Useful commands

To scale containers using docker compose:
```shell
sudo docker build -t locust-mqtt-1 .
sudo docker-compose up -d --scale locust-slave=10
```


# Dockerfile

 Currently is been used a docker-compose file, but you can run manually as you want.

```shell
sudo docker build -t locust-mqtt-1 .
sudo docker run -it -d -p 8089:8089 locust-mqtt-1
sudo docker exec -it <CONTAINER_ID> /bin/bash -c "locust -f iot-publish.py -H <HOST>:1883 --no-web -c <N_CLIENTES> -r <RATE>"
```


# Changing System File Limitations

Basically you edit /etc/security/limits.conf adding:

* hard nofile 500000

* soft nofile 500000

You may also need to modify /etc/sysctl.conf adding:

fs.file-max = 500000
sudo sysctl -p


In order to check the system limits:

```shell
ulimit -a
```
