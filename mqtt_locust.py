import random
import time
import sys
import ssl

import paho.mqtt.client as mqtt
from locust import Locust, task, TaskSet, events

REQUEST_PYTHON = 'PYTHON'
REQUEST_TYPE = 'MQTT'
MESSAGE_TYPE_PUB = 'PUB'
MESSAGE_TYPE_SUB = 'SUB'

def time_delta(t1, t2):
    return int((t2 - t1) * 1000)


def fire_locust_failure(**kwargs):
    events.request_failure.fire(**kwargs)


def fire_locust_success(**kwargs):
    events.request_success.fire(**kwargs)


class LocustError(Exception):
    pass


class TimeoutError(ValueError):
    pass


class ConnectError(Exception):
    pass

class DisconnectError(Exception):
    pass


class Message(object):

    def __init__(self, type, qos, topic, payload, start_time, timeout, name):
        self.type = type,
        self.qos = qos,
        self.topic = topic
        self.payload = payload
        self.start_time = start_time
        self.timeout = timeout
        self.name = name

    def timed_out(self, total_time):
        return self.timeout is not None and total_time > self.timeout


class MQTTClient(mqtt.Client):

    def __init__(self, *args, **kwargs):
        super(MQTTClient, self).__init__(*args, **kwargs)
        self.on_publish = self.locust_on_publish
        self.on_disconnect = self.locust_on_disconnect
        self.on_connect = self.locust_on_connect
        self.pubmmap = {}
        self.defaultQoS = 0
        self.is_connected = False
        fire_locust_success(
            request_type=REQUEST_PYTHON,
            name='MQTT Client created.',
            response_time=0,
            response_length=0
        )


    def connecting(self, host, port):
        print ("Trying to connect to MQTT broker")
        self.start_time = time.time()
        try:
          #self.client.tls_set(self.ca_cert, self.iot_cert, self.iot_private_key, tls_version=ssl.PROTOCOL_TLSv1_2)
          #It is important to do an asynchronous connect, given that we will have
          #multiple connections happening in a single server during a Locust test
          super(MQTTClient, self).connect_async(host=host, port=port, keepalive=600)
          super(MQTTClient, self).loop_start() 
        except Exception as e:
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name='connect',
                response_time=time_delta(self.start_time, time.time()),
                exception=ConnectError("Could not connect to host:["+host+"]")
            )

    def disconnecting(self):
        print ("Closing")
        self.is_connected = False
        super(MQTTClient, self).loop_stop() # stops network loop
        super(MQTTClient, self).disconnect() # disconnect gracefully
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name="Closing",
            response_time=0,
            exception=ConnectError("Connection timeout or lost. Closing connection and removing MQTT client. ")
        )
 

    def reconnecting(self,host, port):
        print ("Reconnecting")
        start_time = time.time()
        super(MQTTClient, self).connect_async(host=host, port=port, keepalive=600)
        super(MQTTClient, self).loop_start() 
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name="reconnecting",
            response_time=time_delta(start_time, time.time()),
            exception=DisconnectError("Connection lost or timeout. Trying to connect to host:["+host+"]")
        )
 

    def publish(self, topic, payload=None, qos=0, retry=5, name='publish', **kwargs):
        timeout = kwargs.pop('timeout', 10000)
        start_time = time.time()
        try:
          res = super(MQTTClient, self).publish(
                    topic,
                    payload=payload,
                    qos=qos,
                    **kwargs
                )
          [ err, mid ] = res
          if err:
            fire_locust_failure(
                    request_type=REQUEST_TYPE,
                    name=name,
                    response_time=time_delta(start_time, time.time()),
                    exception=ValueError(err)
                )

            print ("publish: err,mid:["+str(err)+","+str(mid)+"]")
          self.pubmmap[mid] = Message(
                    MESSAGE_TYPE_PUB, qos, topic, payload, start_time, timeout, name
                    )
          #print ("publish: Saved message - mqtt client obj id:["+str(id(self))+"] - pubmmap obj id:["+str(id(self.pubmmap))+"] in dict - mid:["+str(mid)+"] - message object id:["+str(id(self.pubmmap[mid]))+"]")                        
        except Exception as e:
          fire_locust_failure(
                    request_type=REQUEST_TYPE,
                    name=name,
                    response_time=time_delta(start_time, time.time()),
                    exception=e,
                )
          print (str(e))


 
    def connection_time(self,initial, final):
        delta = time_delta(initial,final)
        name = ""
        if (delta >= 0 and delta < 10 ):
            name="1. Connection time: between 0 and 10 ms"
        if (delta >= 10 and delta < 100 ):
            name="2. Connection time: between 10 and 100 ms"
        if (delta >= 100 and delta < 1000 ):
            name="3. Connection time: between 100 and 1000 ms"
        if (delta >= 1000 and delta < 3000 ):
            name="4. Connection time: between 1 and 3 s"
        if (delta >= 3000 and delta < 8000 ):
            name="5. Connection time: between 3 and 8 s"
        if (delta >= 8000 and delta < 15000 ):
            name="6. Connection time: between 8 and 15 s"
        if (delta >= 15000 and delta < 20000 ):
            name="6. Connection time: between 15 and 20 s"
        if (delta >= 20000):
            name="7. Connection time: higher then 20 s"

        fire_locust_success(
            request_type=REQUEST_TYPE,
            name=name,
            response_time=delta,
            response_length=0,
            )
     
        pass
        

    def warning_connection_down(self):
        print("Warning: Trying publish without connection..")        
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name='No conection. Trying to reconnect.',
            response_time=0,
            exception=None
        )

    def warning_timeout(self):
        print("Warning: More than 20 seconds to connect.")        
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name='Warning: More than 20 seconds to connect.',
            response_time=0,
            exception=None
        )


    def locust_on_connect(self, client, flags_dict, userdata, rc):
        connection_time = time.time()
        print(mqtt.connack_string(rc))        
        if rc == 0:
            self.is_connected = True
        try:
          fire_locust_success(
            request_type=REQUEST_TYPE,
            name='connect',
            response_time=0,
            response_length=0
            )
          self.connection_time(self.start_time, connection_time)
        except Exception as e:
          print("Connection broken")
          print(e)
          fire_locust_failure(
            request_type=REQUEST_TYPE,
            name='connect',
            response_time=0,
            exception=e
            )
        
    
    """
    Paho documentation regarding on_publish event:
    'For messages with QoS levels 1 and 2, this means that the appropriate handshakes have
    completed. For QoS 0, this simply means that the message has left the client.'
    
    This means that the value we record in fire_locust_success for QoS 0 will always
    be very low and not a meaningful metric. The interesting part comes when we analyze 
    metrics emitted by the system on the other side of the MQTT broker (the systems processing
    incoming data from things).
    """
        
    def locust_on_publish(self, client, userdata, mid):
        end_time = time.time()
        
        if self.defaultQoS == 0:
          #if QoS=0, we reach the callback before the publish() has enough time to update the pubmmap dictionary
          time.sleep(float(0.5))

        message = self.pubmmap.pop(mid, None)        
        #print ("on_publish  - mqtt client obj id:["+str(id(self))+"] - pubmmap obj id:["+str(id(self.pubmmap))+"] - mid:["+str(mid)+"] - message obj id:["+str(id(message))+"]")
        if message is None:
          fire_locust_failure(
                request_type=REQUEST_TYPE,
                name="message_found",
                response_time=0,
                exception=ValueError("Published message could not be found"),
          )
          return
        
        total_time = time_delta(message.start_time, end_time)
        if message.timed_out(total_time):
          fire_locust_failure(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                exception=TimeoutError("publish timed out"),
          )
          #print("report publish failure - response_time:["+str(total_time)+"]")
        else:
          fire_locust_success(
            request_type=REQUEST_TYPE,
            name=message.name,
            response_time=total_time,
            response_length=len(message.payload),
            )
          #print("report publish success - response_time:["+str(total_time)+"]")


    def locust_on_disconnect(self, client, userdata, rc):
        print("locust_on_disconnect, RC: ", rc)
        if (self.is_connected):
            self.is_connected = False
            #super(MQTTClient, self).loop_stop() # stops network loop
            #super(MQTTClient, self).disconnect() # stops network loop
            client.loop_stop()
            client.disconnect()
        
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name='disconnect',
            response_time=0,
            exception=DisconnectError("disconnected"),
        )
        #self.reconnect()



class MQTTLocust(Locust):

    def __init__(self, *args, **kwargs):
        print("initializing MQTTLocust")
        # TODO update args to receive hosts passed by config files
        super(Locust, self).__init__(*args, **kwargs)
        # try:
        #     [host, port] = self.host.split(":")
        # except:
        #     host, port = self.host, 1883