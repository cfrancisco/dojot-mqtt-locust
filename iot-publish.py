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
from mqtt_locust import MQTTLocust, MQTTClient
import random
import resource

# set logger
logger = logging.getLogger('dojot')
logger.setLevel(logging.DEBUG)

# default data
data = dict()

data['device_id'] = "2a2s2e1"
#data['dojot_host'] = "10.50.11.155"
#data['dojot_port'] = "30001"
data['dojot_host'] = "10.4.2.28"
data['dojot_port'] = "8000"

co = dict()
co['host'] = "10.50.11.160"
co['port'] = "30002"
ct = dict()
ct['host'] = "10.4.2.28"
ct['port'] = "1883"

data['host_availables'] = [ct, co]

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

    #def on_start(self):
    #     print ("Creating Device.")
    #     # do login
    #     auth_header = do_login(secure, data['dojot_host'], user, password, data['dojot_port'])
    #     # create devices
    #     self.devices_available = []
    #     aux_prefix = self.clnt.clnt_id 
    #     self.devices_available = create_devices(auth_header,
    #                             data['template_id'],
    #                             secure,
    #                             data['dojot_host'],
    #                             number_of_devices,
    #                             aux_prefix,
    #                             data['dojot_port'])
    #     time.sleep(4)

    def on_stop(self):
        if self.clnt.is_connected:
            print ("Client is connected so let's disconnect the tasks")
            self.clnt.disconnecting()
        pass

    @task
    class SubDevice(TaskSet):

        def loop_until_connected(self):
            attempts = 0
            while (attempts < 20):
              if (not self.clnt.is_connected):
                time.sleep(1)
                attempts+=1
              else:
                break
            print("Finished loop with {} attempts.".format(attempts))
            #if (attempts == 20):
            #    self.clnt.warning_timeout()

        def on_start(self):
            print("Starting SubTask....")
            self.current_host = 0
            self.getHost(self.current_host)
            self.create_and_connect()
        
        def getHost(self, index):
            self.last_connected_host = data['host_availables'][index]['host'] 
            self.last_connected_port = data['host_availables'][index]['port'] 

                
        def changeHost(self):
            self.current_host = self.current_host+1
            if (self.current_host >= len(data['host_availables'])):
                self.current_host = 0
            self.getHost(self.current_host)
            print("Changing to host: "+self.last_connected_host)

        def create_and_connect(self):
            # creating new client
            self.clnt_id = "{0}-{1}-{2}".format("locust", random.randint(1,10000),random.randint(1,10000))
            self.clnt = MQTTClient(self.clnt_id)
            self.clnt.connecting(host = self.last_connected_host, port = self.last_connected_port)
            self.loop_until_connected()

        @task
        def publish(self):
            #print ("publish task called")
            if not self.clnt.is_connected:
                self.changeHost()
                # disconnect the old client
                self.clnt.disconnecting()
                # creating new client
                self.clnt = None
                self.create_and_connect()
                #self.interrupt()
                return False
            device_id = data['device_id']
            topic = "/{0}/{1}/attrs".format(tenant, device_id)
            self.clnt.publish(
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
    # create the template and the device used in all requests
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

    #createTemplateAndDevice()

    task_set = IotDevice
    min_wait = 10000 # 10 segs
    max_wait = 10000 # 10 segs
