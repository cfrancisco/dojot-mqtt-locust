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
from dojot_devices import (do_login, create_devices, create_template)
from mqtt_locust import MQTTLocust
import random
import resource

# set logger
logger = logging.getLogger('dojot')
logger.setLevel(logging.DEBUG)

# default data
data = dict()
#data['host'] = "iotmid-docker.cpqd.com.br"
#data['mqtt_port'] = "1883"

data['host'] = "10.50.11.160"
data['mqtt_port'] = "30002"
data['dojot_host'] = "10.50.11.155"
data['dojot_port'] = "30001"

#topic
tenant = "admin"
publish_timeout = 20000

#device options
secure = False
user = 'admin'
password = 'admin'
number_of_devices = 1
prefix = 'locust'



class IotDevice(TaskSet):

    def on_start(self):
        return True
        print ("Creating Device.")
        
        # do login
        auth_header = do_login(secure, data['dojot_host'], user, password, data['dojot_port'])
        
        # create devices
        self.devices_available = []
        aux_prefix = self.client.client_id 
        self.devices_available = create_devices(auth_header,
                                data['template_id'],
                                secure,
                                data['dojot_host'],
                                user,
                                password,
                                number_of_devices,
                                aux_prefix,
                                data['dojot_port'])
        time.sleep(4)
            

    def on_stop(self):
        if self.client.is_connected:
            print ("Client is connected so let's disconnect the tasks")
            self.client.disconnecting()
        pass

    @task
    class SubDevice(TaskSet):

        def on_start(self):
            print("Starting SubTask....")
            print ("Trying to connect to MQTT broker")
            self.client.connecting()
            time.sleep(5)
            #allow for the connection to be established before doing anything (publishing or subscribing) to the MQTT topic
            
        @task
        def publish(self):
            #print ("publish task called")
            if not self.client.is_connected:
                print ("Connection state to publish: ", self.client.is_connected)
                self.client.reconnecting()
                time.sleep(5)
                #self.interrupt()
                return False
            return True
            #device_id = random.choice(self.devices_available)
            device_id = self.parent.devices_available[0]
            topic = "/{0}/{1}/attrs".format(tenant, device_id)
            self.client.publish(
                topic=topic,
                payload=self.payload(),
                qos=0,
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
    auth_header = do_login(secure, data['dojot_host'], user, password, data['dojot_port'])
    # now, let's create the template
    data['template_id'] = create_template(auth_header,
                                secure,
                                data['dojot_host'],
                                'locust',
                                data['dojot_port'])

def getParms():
    argss = sys.argv[1:]
    host = argss[argss.index("-H")+1]
    [host, mqtt_port] = host.split(":")
    data['host'] = host
    data['dojot_host'] = host
    data['mqtt_port'] = mqtt_port
    logger.info("Host: {}".format(host))

class MyThing(MQTTLocust):
    logger.info("Running!")

    #updateLimits()

    # Isn't possible uses -H and slave/master schema in the same
    # time. Thus, for now, the host and port were hard coded.
    #getParms()

    createTemplate()

    task_set = IotDevice
    min_wait = 10
    max_wait = 100