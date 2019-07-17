import requests
import logging
import uuid
# TODO: handle errors

logger = logging.getLogger('dojot.devices')

def do_login(secure, host, user, password, port=8000):
    # Get JWT token
    if secure:
        url = 'https://{}/auth'.format(host)
    else:
        url = 'http://{0}:{1}/auth'.format(host,port)
    data = {"username" : "{}".format(user), "passwd" : "{}".format(password)}
    response = requests.post(url=url, json=data)
    token = response.json()['jwt']
    logger.info("Successfully logged in Dojot.")
    if response.status_code != 200:
        print (str(response))
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))
    auth_header = {"Authorization": "Bearer {}".format(token)}
    return auth_header


def create_template(auth_header, secure, host, prefix='no-prefix', port=8000):
    # Create Template
    if secure:
        url = 'https://{}/template'.format(host)
    else:
        url = 'http://{0}:{1}/template'.format(host,port)
    data = {"label": "{}".format(prefix),
            "attrs" : [{"label": "protocol",
                        "type": "static",
                        "value_type": "string",
                        "static_value":"mqtt"},
                        {"label": "temperature",
                        "type": "dynamic",
                        "value_type": "float"}, 
                        {"label" : "gps",
                        "type" : "dynamic",
                        "value_type" : "geo:point"}]}
    response = requests.post(url=url, headers=auth_header, json=data)
    if response.status_code != 200:
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))
    template_id = response.json()['template']['id']
    return template_id

def create_devices(auth_header, template_id, secure, host, number_of_devices, prefix='no-prefix', port=8000):
    devices = []

    # Create devices
    if secure:
        url = 'https://{}/device'.format(host)
    else:
        url = 'http://{0}:{1}/device'.format(host,port)
    for n in range(1,number_of_devices+1):
        data = {"templates" : ["{}".format(template_id)],
                "label" : "{0}-{1}".format(prefix,n)}
        response = requests.post(url=url, headers=auth_header, json=data)
        if response.status_code != 200:
            raise Exception("HTTP POST failed {}.".
                            format(response.status_code))
        device_id = response.json()['devices'][0]['id']
        if response.status_code != 200:
            raise Exception("HTTP POST failed {}.".
                            format(response.status_code))
        devices.append(device_id)

        # Set serial number
        if secure:
            url_update = 'https://{}/device/{}'.format(host, device_id)
        else:
            url_update = 'http://{}:{}/device/{}'.format(host, port, device_id)
 
        # Get
        response = requests.get(url=url_update, headers=auth_header)
        if response.status_code != 200:
            raise Exception("HTTP POST failed {}.".
                            format(response.status_code))
        data = response.json()
        attrs_static = []
        for attribute in data['attrs']["{}".format(template_id)]:
            if attribute['type'] == 'static':
                if attribute['label'] == 'serial':
                    attribute['static_value'] = uuid.uuid4().hex
                    attribute['static_value'] = attribute['static_value']
                attrs_static.append(attribute)
        data['attrs'] = attrs_static

        # Put
        response = requests.put(url=url_update, headers=auth_header, json=data)
        if response.status_code != 200:
            raise Exception("HTTP POST failed {}.".
                            format(response.status_code))

    logger.info("Created devices: {}".format(devices))

    return devices



def create_template_and_device(auth_header, secure, host, prefix='no-prefix', port=8000):
    # Create Template
    if secure:
        url = 'https://{}/template'.format(host)
    else:
        url = 'http://{0}:{1}/template'.format(host,port)
    data = {"label": "{}".format(prefix),
            "attrs" : [{"label": "protocol",
                        "type": "static",
                        "value_type": "string",
                        "static_value":"mqtt"},
                        {"label": "temperature",
                        "type": "dynamic",
                        "value_type": "float"}, 
                        {"label" : "gps",
                        "type" : "dynamic",
                        "value_type" : "geo:point"}]}
    response = requests.post(url=url, headers=auth_header, json=data)
    if response.status_code != 200:
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))
    template_id = response.json()['template']['id']
    logger.info("Created Template: {}".format(template_id))

    # Create devices
    if secure:
        url = 'https://{}/device'.format(host)
    else:
        url = 'http://{0}:{1}/device'.format(host,port)
    data = {"templates" : ["{}".format(template_id)],
            "label" : "{0}-{1}".format(prefix,1)}
    response = requests.post(url=url, headers=auth_header, json=data)
    if response.status_code != 200:
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))
    device_id = response.json()['devices'][0]['id']
    if response.status_code != 200:
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))

    logger.info("Created device: {}".format(device_id))

    return device_id


