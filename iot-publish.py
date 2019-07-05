# -*- coding: utf-8 -*-
import json
import random
import resource
import ssl
import time
import os
import logging
import sys


from locust import TaskSet, task
from dojot_devices import (do_login, create_devices, create_template, remove_devices)
from mqtt_locust import MQTTLocust
import random
import resource

# set logger
logger = logging.getLogger('dojot')
logger.setLevel(logging.DEBUG)

# default data
data = dict()
data['host'] = "localhost"
data['mqtt_port'] = "1883"

#topic
tenant = "admin"
publish_timeout = 20000

#device options
secure = False
user = 'admin'
password = 'admin'
number_of_devices = 1
prefix = 'locust'



class ThingBehavior(TaskSet):
    def on_start(self):
        # do login
        auth_header = do_login(secure, data['host'], user, password)
        # create devices
        self.devices_available = []
        aux_prefix = "{0}-{1}".format(prefix, random.randint(1,1001))
        self.devices_available = create_devices(auth_header,
                                 data['template_id'],
                                 secure,
                                 data['host'],
                                 user,
                                 password,
                                 number_of_devices,
                                 aux_prefix)

        #allow for the connection to be established before doing anything (publishing or subscribing) to the MQTT topic
        time.sleep(5)

    def device_creation(self):
        self.devices_available = self.devices_available + create_devices(auth_header,
                                 secure,
                                 gw,
                                 user,
                                 password,
                                 number_of_devices,
                                 prefix)

    @task
    def publish(self):
        #print ("publish task called")
        #device_id = random.choice(self.devices_available)
        device_id = self.devices_available[0]
        topic = "/{0}/{1}/attrs".format(tenant, device_id)
        self.client.publish(
            payload=self.payload(),
            qos=0,
            topic=topic,
            name=topic,
            timeout=publish_timeout)

    def payload(self):
        payload = {
           'temperature': random.randrange(0,10,1) #set temperature between 0 and 10
           } 
        return json.dumps(payload)


"""
   Locust hatches several instances of this class, according to the number of simulated users
   that we define in the GUI. Each instance of MyThing represents a device that will connect to IoT Middleware.
"""


def updateLimits():
    logger.info("Setting new limits to files.")
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    print (soft, hard)
    # setting new limits
    resource.setrlimit(resource.RLIMIT_NOFILE, (1048576, 1048576))
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    print (soft, hard)

def createTemplate():
    logger.info("Creating template.")
    # do login
    auth_header = do_login(secure, data['host'], user, password)
    # now, let's create the template
    data['template_id'] = create_template(auth_header,
                                secure,
                                data['host'],
                                'locust')

def getParms():
    argss = sys.argv[1:]
    host = argss[argss.index("-H")+1]
    [host, mqtt_port] = host.split(":")
    data['host'] = host
    data['mqtt_port'] = mqtt_port
    logger.info("Host: {}".format(host))

class MyThing(MQTTLocust):
    logger.info("Running!")

    #updateLimits()

    # Isn't possible uses -H and slave/master schema in the same
    # time. Thus, for now, the host and port were hard coded
    #getParms()

    createTemplate()

    task_set = ThingBehavior
    min_wait = 3
    max_wait = 10