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
from dojot_devices import (do_login, create_devices, create_template_and_device)
from mqtt_locust import MQTTLocust
import random
import resource

# set logger
logger = logging.getLogger('dojot')
logger.setLevel(logging.DEBUG)

# default data
data = dict()

data['dojot_host'] = "10.50.11.155"
data['dojot_port'] = "30001"
data['mqtt_host'] = "10.50.11.160"
data['mqtt_port'] = "30002"

#Anderson
#data['mqtt_host'] = "10.202.70.18"
#data['mqtt_port'] = "1883"

#iotmid-docekr
#data['dojot_host'] = "10.4.2.28"
#data['dojot_port'] = "8000"
#data['mqtt_host'] = "10.4.2.28"
#data['mqtt_port'] = "1883"

#joab
#data['mqtt_host'] = "10.202.70.99"
#data['mqtt_port'] = "1883"

#me
#data['mqtt_host'] = 'localhost'
#data['mqtt_port'] = '1883'



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

    # def on_start(self):
    #     print ("Creating Device.")

    #     # do login
    #     auth_header = do_login(secure, data['dojot_host'], user, password, data['dojot_port'])
        
    #     # create devices
    #     self.devices_available = []
    #     aux_prefix = self.client.client_id 
    #     self.devices_available = create_devices(auth_header,
    #                             data['template_id'],
    #                             secure,
    #                             data['dojot_host'],
    #                             number_of_devices,
    #                             aux_prefix,
    #                             data['dojot_port'])
    #     time.sleep(4)
            

    def on_stop(self):
        if self.client.is_connected:
            print ("Client is connected so let's disconnect the tasks")
            self.client.disconnecting()
        pass

    @task
    class SubDevice(TaskSet):

        def loop_until_connected(self):
            #print("Starting loop.")
            attempts = 0
            while (attempts < 30):
              if (not self.client.is_connected):
                time.sleep(1)
                attempts+=1
              else:
                break
            print("Finished loop with {} attempts.".format(attempts))
            if (attempts == 30):
                self.client.warning_timeout()

        def on_start(self):
            print("Starting SubTask....")
            self.client.connecting(host = data['mqtt_host'], port =  
            data['mqtt_port'])
            self.loop_until_connected()


        @task
        def publish(self):
            #print ("publish task called")
            if not self.client.is_connected:
                print ("Connection is down. ")
                self.client.reconnecting(host = data['mqtt_host'], port =  data['mqtt_port'])
                self.loop_until_connected()
                #self.interrupt()
                return False
            #device_id = random.choice(self.devices_available)
            #device_id = self.parent.devices_available[0]
            device_id = data['device_id']
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



def createTemplateAndDevice():
    # do login
    auth_header = do_login(False, data['dojot_host'], user, password, data['dojot_port'])
    # now, let's create the template
    data['device_id'] = create_template_and_device(auth_header,
                                False,
                                data['dojot_host'],
                                'locust',
                                data['dojot_port'])

def getParms():
    argss = sys.argv[1:]
    host = argss[argss.index("-H")+1]
    [host, mqtt_port] = host.split(":")
    data['mqtt_host'] = host
    data['dojot_host'] = host
    data['mqtt_port'] = mqtt_port
    logger.info("Host: {}".format(host))


class MyThing(MQTTLocust):
    logger.info("Running!")

    # Isn't possible uses -H and slave/master schema in the same
    # time. Thus, for now, the host and port were hard coded.
    #getParms()

    createTemplateAndDevice()

    task_set = IotDevice
    min_wait = 10000 # 10 segs
    max_wait = 10000 # 10 segs
