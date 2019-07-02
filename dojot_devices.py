import requests
import logging
import uuid
# TODO: handle errors

logger = logging.getLogger('dojot.devices')

def do_login(secure, host, user, password):
    # Get JWT token
    if secure:
        url = 'https://{}/auth'.format(host)
    else:
        url = 'http://{}:8000/auth'.format(host)
    data = {"username" : "{}".format(user), "passwd" : "{}".format(password)}
    response = requests.post(url=url, json=data)
    token = response.json()['jwt']
    logger.info("Logged: {}".format(token))
    if response.status_code != 200:
        print (str(response))
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))
    auth_header = {"Authorization": "Bearer {}".format(token)}
    return auth_header


def create_template(auth_header, secure, host, prefix='no-prefix'):
    # Create Template
    if secure:
        url = 'https://{}/template'.format(host)
    else:
        url = 'http://{}:8000/template'.format(host)
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

def create_devices(auth_header, template_id, secure, host, user, password, number_of_devices, prefix='no-prefix'):
    devices = []

    # Create devices
    if secure:
        url = 'https://{}/device'.format(host)
    else:
        url = 'http://{}:8000/device'.format(host)
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
            url_update = 'http://{}:8000/device/{}'.format(host, device_id)
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


def remove_devices(secure, host, user, password, prefix='trackingsim'):
    # Get JWT token
    if secure:
        url = 'https://{}/auth'.format(host)
    else:
        url = 'http://{}:8000/auth'.format(host)
    data = {"username" : "{}".format(user), "passwd" : "{}".format(password)}
    response = requests.post(url=url, json=data)
    if response.status_code != 200:
        raise Exception("HTTP POST failed {}.".
                        format(response.status_code))
    token = response.json()['jwt']
    auth_header = {"Authorization": "Bearer {}".format(token)}

    # Get devices
    # TODO handle pagination
    if secure:
        url = 'https://{}/device?page_size=128'.format(host)
    else:
        url = 'http://{}:8000/device?page_size=128'.format(host)
    response = requests.get(url=url, headers=auth_header)
    if response.status_code != 200:
        raise Exception("HTTP GET failed {}.".
                        format(response.status_code))
    all_devices = list(response.json()['devices'])

    devices_to_be_removed = []
    for dev in all_devices:
        if dev['label'].startswith(prefix):
            devices_to_be_removed.append(dev['id'])

    # Remove devices
    removed_devices = []
    for dev in devices_to_be_removed:
        if secure:
            url = 'https://{0}/device/{1}'.format(host, dev)
        else:
            url = 'http://{0}:8000/device/{1}'.format(host, dev)
        response = requests.delete(url=url, headers=auth_header)
        if response.status_code == requests.codes.ok:
            removed_devices.append(dev)
        else:
            logger.error("Failed to remove device {}".format(dev))

    logger.info("Removed devices: {}".format(removed_devices))

    # Get templates
    # TODO handle pagination
    if secure:
        url = 'https://{}/template?page_size=1000'.format(host)
    else:
        url = 'http://{}:8000/template?page_size=1000'.format(host)
    response = requests.get(url=url, headers=auth_header)
    if response.status_code != 200:
        raise Exception("HTTP GET failed {}.".
                        format(response.status_code))
    all_templates = list(response.json()['templates'])

    templates_to_be_removed = []
    for tpl in all_templates:
        if tpl['label'].startswith(prefix):
            templates_to_be_removed.append(tpl['id'])

    # Remove templates
    removed_templates = []
    for tpl in templates_to_be_removed:
        if secure:
            url = 'https://{0}/template/{1}'.format(host, tpl)
        else:
            url = 'http://{0}:8000/template/{1}'.format(host, tpl)
        response = requests.delete(url=url, headers=auth_header)
        if response.status_code == requests.codes.ok:
            removed_templates.append(tpl)
        else:
            logger.error("Failed to remove template {}".format(tpl))

    logger.info("Removed templates: {}".format(removed_templates))
