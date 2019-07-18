import random
import time
import sys
import ssl

import paho.mqtt.client as mqtt
from locust import Locust, task, TaskSet, events

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
        self.on_subscribe = self.locust_on_subscribe
        self.on_disconnect = self.locust_on_disconnect
        self.on_connect = self.locust_on_connect
        self.pubmmap = {}
        self.submmap = {}
        self.defaultQoS = 0
        self.is_connected = False


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
        print ("Disconnecting")
        super(MQTTClient, self).disconnect() # disconnect gracefully
        super(MQTTClient, self).loop_stop() # stops network loop
        self.is_connected = False

    def reconnecting(self,host, port):
        print ("Reconnecting")
        start_time = time.time()
        super(MQTTClient, self).connect_async(host=host, port=port, keepalive=600)
        super(MQTTClient, self).loop_start() 
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name="reconnecting",
            response_time=time_delta(start_time, time.time()),
            exception=DisconnectError("Connection is down. Trying to reconnect.")
        )


    def publish(self, topic, payload=None, qos=0, retry=5, name='publish', **kwargs):
        #print ("publishing", self.is_connected)
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


    #retry is not used at the time since this implementation only supports QoS 0
    def subscribe(self, topic, qos=0, retry=5, name='subscribe', timeout=15000):
        #print ("subscribing to topic:["+topic+"]")
        start_time = time.time()
        try:
            err, mid = super(MQTTClient, self).subscribe(
                  topic,
                  qos=qos
            )
            self.submmap[mid] = Message(
                    MESSAGE_TYPE_SUB, qos, topic, "", start_time, timeout, name
                      )
            if err:
              raise ValueError(err)
              print ("Subscribed to topic with err:["+str(err)+"]messageId:["+str(mid)+"]")
        except Exception as e:
          total_time = time_delta(start_time, time.time())
          fire_locust_failure(
                  request_type=REQUEST_TYPE,
                  name=name,
                  response_time=total_time,
                  exception=e,
          )
          print ("Exception when subscribing to topic:["+str(e)+"]")
        

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
        if (delta >= 15000 and delta < 30000 ):
            name="6. Connection time: between 15 and 30 s"
        if (delta >= 30000):
            name="7. Connection time: higher then 30 s"

        fire_locust_success(
            request_type=REQUEST_TYPE,
            name=name,
            response_time=delta,
            response_length=0,
            )
     
        pass
        

    def warning_timeout(self):
        print("Warning: More than 30 seconds to connect.")        
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name='Warning: More than 30 seconds to connect.',
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


    def locust_on_subscribe(self, client, userdata, mid, granted_qos):
        end_time = time.time()
        message = self.submmap.pop(mid, None)
        if message is None:
            print ("did not find message for on_subscribe")
            return
        total_time = time_delta(message.start_time, end_time)
        if message.timed_out(total_time):
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                exception=TimeoutError("subscribe timed out"),
            )
            print("report subscribe failure - response_time:["+str(total_time)+"]")
        else:
            fire_locust_success(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                response_length=0,
            )
            print("report subscribe success - response_time:["+str(total_time)+"]")
        

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
        super(Locust, self).__init__(*args, **kwargs)

        #TODO: Current implementation sets an empty client_id when the connection is initialized,
        #      which Paho handles by creating a random client_id. 
        #		Ideally we want to control the client_id that is set in Paho. Each client_id
        #		should match a thing_id in the AWS IoT Thing Registry
        self.client_id = "{0}-{1}-{2}".format("locust", random.randint(1,111233),random.randint(1,111233))
        self.client = MQTTClient(self.client_id)

        # try:
        #     [host, port] = self.host.split(":")
        # except:
        #     host, port = self.host, 1883
        # port = int(port)
        # # set data
        # self.client.client_id = self.client_id
        # self.client.host = host
        # self.client.port = port 
        