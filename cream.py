"""
Class to configure Cisco ISE via the ERS API
"""
import json
import os
import re

import requests

base_dir = os.path.dirname(__file__)


class InvalidMacAddress(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ERS(object):
    def __init__(self, ise_node, ers_user, ers_pass, verify=False, disable_warnings=False, timeout=2):
        """
        Class to interact with Cisco ISE via the ERS API
        :param ise_node: IP Address of the primary admin ISE node
        :param ers_user: ERS username
        :param ers_pass: ERS password
        :param verify: Verify SSL cert
        :param disable_warnings: Disable requests warnings
        :param timeout: Query timeout
        """
        self.ise_node = ise_node
        self.user_name = ers_user
        self.user_pass = ers_pass

        self.url_base = 'https://{0}:9060/ers'.format(self.ise_node)
        self.ise = requests.session()
        self.ise.auth = (self.user_name, self.user_pass)
        self.ise.verify = verify  # http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
        self.disable_warnings = disable_warnings
        self.timeout = timeout
        self.ise.headers.update({'Connection': 'keep_alive'})

        if self.disable_warnings:
            requests.packages.urllib3.disable_warnings()


    @staticmethod
    def _mac_test(mac):
        """
        Test for valid mac address
        :param mac: MAC address in the form of AA:BB:CC:00:11:22
        :return: True/False
        """

        if re.search(r'([0-9A-F]{2}[:]){5}([0-9A-F]){2}', mac.upper()) is not None:
            return True
        else:
            return False

    def get_endpoint_groups(self):
        """
        Get all endpoint identity groups
        :return: result dictionary
        """
        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/endpointgroup'.format(self.url_base))

        if resp.status_code == 200:
            result['success'] = True
            result['response'] = [(i['name'], i['id'], i['description']) for i in resp.json()['SearchResult']['resources']]

            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_endpoint_group(self, group):
        """
        Get endpoint identity group details
        :param group: Name of the identity group
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/endpointgroup?filter=name.EQ.{1}'.format(self.url_base, group))
        found_group = resp.json()

        if found_group['SearchResult']['total'] == 1:
            resp = self.ise.get('{0}/config/endpointgroup/{1}'.format(self.url_base, found_group['SearchResult']['resources'][0]['id']))
            if resp.status_code == 200:
                result['success'] = True
                result['response'] = resp.json()['EndPointGroup']
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(group)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_group['SearchResult']['total'] == 0:
            result['response'] = '{0} not found'.format(group)
            result['error'] = 404
            return result

        else:
            result['response'] = '{0} not found'.format(group)
            result['error'] = resp.status_code
            return result

    def get_endpoints(self):
        """
        Get all endpoints
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/endpoint'.format(self.url_base))

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        json_res = resp.json()['SearchResult']

        if resp.status_code == 200 and int(json_res['total']) > 1:
            result['success'] = True
            result['response'] = [(i['name'], i['id'])
                                  for i in json_res['resources']]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 1:
            result['success'] = True
            result['response'] = [(json_res['resources'][0]['name'],
                                   json_res['resources'][0]['id'])]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 0:
            result['success'] = True
            result['response'] = []
            return result

        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_endpoint(self, mac_address):
        """
        Get endpoint details
        :param mac_address: MAC address of the endpoint
        :return: result dictionary
        """
        is_valid = ERS._mac_test(mac_address)

        if not is_valid:
            raise InvalidMacAddress('{0}. Must be in the form of AA:BB:CC:00:11:22'.format(mac_address))
        else:
            self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

            result = {
                'success': False,
                'response': '',
                'error': '',
            }

            resp = self.ise.get('{0}/config/endpoint?filter=mac.EQ.{1}'.format(self.url_base, mac_address))
            found_endpoint = resp.json()

            if found_endpoint['SearchResult']['total'] == 1:
                resp = self.ise.get('{0}/config/endpoint/{1}'.format(
                        self.url_base, found_endpoint['SearchResult']['resources'][0]['id']))
                if resp.status_code == 200:
                    result['success'] = True
                    result['response'] = resp.json()['ERSEndPoint']
                    return result
                elif resp.status_code == 404:
                    result['response'] = '{0} not found'.format(mac_address)
                    result['error'] = resp.status_code
                    return result
                else:
                    result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                    result['error'] = resp.status_code
                    return result
            elif found_endpoint['SearchResult']['total'] == 0:
                result['response'] = '{0} not found'.format(mac_address)
                result['error'] = 404
                return result

            else:
                result['response'] = '{0} not found'.format(mac_address)
                result['error'] = resp.status_code
                return result

    def search_endpoints_by_group(self, group_id):
        """
        Get all endpoints
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        print('{0}/config/endpoint?filter=identityGroup.EQ.{1}'.format(self.url_base, group_id))

        resp = self.ise.get('{0}/config/endpoint?filter=groupId.EQ.{1}'.format(self.url_base, group_id))

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        json_res = resp.json()['SearchResult']

        if resp.status_code == 200 and int(json_res['total']) > 1:
            result['success'] = True
            result['response'] = [(i['name'], i['id'])
                                  for i in json_res['resources']]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 1:
            result['success'] = True
            result['response'] = [(json_res['resources'][0]['name'],
                                   json_res['resources'][0]['id'])]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 0:
            result['success'] = True
            result['response'] = []
            return result

        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def list_endpoints_in_group(self, group_id, page=1):
        """
        Get all endpoints
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        #print('{0}/config/endpoint?size=100&filter=identityGroup.EQ.{1}&page={2}'.format(self.url_base, group_id, page))

        resp = self.ise.get('{0}/config/endpoint?size=100&filter=groupId.EQ.{1}&page={2}'.format(self.url_base, group_id, page))

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        json_res = resp.json()['SearchResult']

        if resp.status_code == 200 and int(json_res['total']) > 100:
            result['success'] = True
            result['response'] = [(i['name'])
                                  for i in json_res['resources']]
            result['total'] = json_res['total']
            #result['next'] = True if ('nextPage' in json_res) else False
            if 'nextPage' in json_res:
                result['next'] = True
            else:
                result['next'] = False
            return result

        if resp.status_code == 200 and int(json_res['total']) > 1:
            result['success'] = True
            result['response'] = [(i['name'])
                                  for i in json_res['resources']]
            result['total'] = json_res['total']
            if 'nextPage' in json_res:
                result['next'] = True
            else:
                result['next'] = False
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 1:
            result['success'] = True
            result['response'] = [(json_res['resources'][0]['name'])]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 0:
            result['success'] = True
            result['response'] = []
            return result

        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def add_endpoint(self,
                    name,
                    mac,
                    group_id,
                    static_profile_assigment='false',
                    static_group_assignment='true',
                    profile_id='',
                    description=''):
        """
        Add a user to the local user store
        :param name: Name
        :param mac: Macaddress
        :param group_id: OID of group to add endpoint in
        :param static_profile_assigment: Set static profile
        :param static_group_assignment: Set static group
        :param profile_id: OID of profile
        :param description: User description
        :return: result dictionary
        """

        is_valid = ERS._mac_test(mac)
        if not is_valid:
            raise InvalidMacAddress('{0}. Must be in the form of AA:BB:CC:00:11:22'.format(mac))
        else:
            self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

            result = {
                'success': False,
                'response': '',
                'error': '',
            }

            data = { "ERSEndPoint" : { 'name': name, 'description': description, 'mac': mac,
                                       'profileId': profile_id, 'staticProfileAssignment': static_profile_assigment,
                                       'groupId': group_id, 'staticGroupAssignment': static_group_assignment,
                                        'customAttributes': {'customAttributes': {'key1': 'value1'} } } }

            resp = self.ise.post('{0}/config/endpoint'.format(self.url_base), data=json.dumps(data), timeout=self.timeout)
            if resp.status_code == 201:
                result['success'] = True
                result['response'] = '{0} Added Successfully'.format(name)
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result


    def delete_endpoint(self, mac):
        """
        Delete an endpoint
        :param mac: Endpoint Macaddress
        :return: Result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/endpoint?filter=mac.EQ.{1}'.format(self.url_base, mac))
        found_endpoint = resp.json()
        if found_endpoint['SearchResult']['total'] == 1:
            endpoint_oid = found_endpoint['SearchResult']['resources'][0]['id']
            resp = self.ise.delete('{0}/config/endpoint/{1}'.format(self.url_base, endpoint_oid), timeout=self.timeout)

            if resp.status_code == 204:
                result['success'] = True
                result['response'] = '{0} Deleted Successfully'.format(mac)
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(mac)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_endpoint['SearchResult']['total'] == 0:
                result['response'] = '{0} not found'.format(mac)
                result['error'] = 404
                return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result



    def get_identity_groups(self):
        """
        Get all identity groups
        :return: result dictionary
        """
        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/identitygroup'.format(self.url_base))

        if resp.status_code == 200:
            result['success'] = True
            result['response'] = [(i['name'], i['id'], i['description'])
                                  for i in resp.json()['SearchResult']['resources']]
            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_identity_group(self, group):
        """
        Get identity group details
        :param group: Name of the identity group
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/identitygroup?filter=name.EQ.{1}'.format(self.url_base, group))
        found_group = resp.json()

        if found_group['SearchResult']['total'] == 1:
            resp = self.ise.get('{0}/config/identitygroup/{1}'.format(
                    self.url_base, found_group['SearchResult']['resources'][0]['id']))
            if resp.status_code == 200:
                result['success'] = True
                result['response'] = resp.json()['IdentityGroup']
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(group)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_group['SearchResult']['total'] == 0:
            result['response'] = '{0} not found'.format(group)
            result['error'] = 404
            return result

        else:
            result['response'] = '{0} not found'.format(group)
            result['error'] = resp.status_code
            return result

    def get_users(self):
        """
        Get all internal users
        :return: List of tuples of user details
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/internaluser'.format(self.url_base))

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        json_res = resp.json()['SearchResult']

        if resp.status_code == 200 and int(json_res['total']) > 1:
            result['success'] = True
            result['response'] = [(i['name'], i['id'])
                                  for i in json_res['resources']]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 1:
            result['success'] = True
            result['response'] = [(json_res['resources'][0]['name'],
                                   json_res['resources'][0]['id'])]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 0:
            result['success'] = True
            result['response'] = []
            return result

        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_user(self, user_id):
        """
        Get user detailed info
        :param user_id: User ID
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/internaluser?filter=name.EQ.{1}'.format(self.url_base, user_id))
        found_user = resp.json()

        if found_user['SearchResult']['total'] == 1:
            resp = self.ise.get('{0}/config/internaluser/{1}'.format(
                    self.url_base, found_user['SearchResult']['resources'][0]['id']))
            if resp.status_code == 200:
                result['success'] = True
                result['response'] = resp.json()['InternalUser']
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(user_id)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_user['SearchResult']['total'] == 0:
            result['response'] = '{0} not found'.format(user_id)
            result['error'] = 404
            return result
        else:
            result['response'] = 'Unknown error'
            result['error'] = resp.status_code
            return result

    def add_user(self,
                 user_id,
                 password,
                 user_group_oid,
                 enable='',
                 first_name='',
                 last_name='',
                 email='',
                 description=''):
        """
        Add a user to the local user store
        :param user_id: User ID
        :param password: User password
        :param user_group_oid: OID of group to add user to
        :param enable: Enable password used for Tacacs
        :param first_name: First name
        :param last_name: Last name
        :param email: email address
        :param description: User description
        :return: result dictionary
        """
        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        data = { "InternalUser" : { 'name': user_id, 'password': password, 'enablePassword': enable,
                                   'firstName': first_name, 'lastName': last_name, 'email': email,
                                   'description': description, 'identityGroups': user_group_oid }}



        resp = self.ise.post('{0}/config/internaluser'.format(self.url_base), data=json.dumps(data), timeout=self.timeout)
        if resp.status_code == 201:
            result['success'] = True
            result['response'] = '{0} Added Successfully'.format(user_id)
            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def delete_user(self, user_id):
        """
        Delete a user
        :param user_id: User ID
        :return: Result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/internaluser?filter=name.EQ.{1}'.format(self.url_base, user_id))
        found_user = resp.json()

        if found_user['SearchResult']['total'] == 1:
            user_oid = found_user['SearchResult']['resources'][0]['id']
            resp = self.ise.delete('{0}/config/internaluser/{1}'.format(self.url_base, user_oid), timeout=self.timeout)

            if resp.status_code == 204:
                result['success'] = True
                result['response'] = '{0} Deleted Successfully'.format(user_id)
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(user_id)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_user['SearchResult']['total'] == 0:
            result['response'] = '{0} not found'.format(user_id)
            result['error'] = 404
            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_device_groups(self):
        """
        Get a list tuples of device groups
        :return:
        """
        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/networkdevicegroup'.format(self.url_base))

        if resp.status_code == 200:
            result['success'] = True
            result['response'] = [(i['name'], i['id'])
                                  for i in resp.json()['SearchResult']['resources']]
            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_device_group(self, device_group_oid):
        """
        Get a device group details
        :param device_group_oid: oid of the device group
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/networkdevicegroup/{1}'.format(self.url_base, device_group_oid))

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        if resp.status_code == 200:
            result['success'] = True
            result['response'] = resp.json()['NetworkDeviceGroup']
            return result
        elif resp.status_code == 404:
            result['response'] = '{0} not found'.format(device_group_oid)
            result['error'] = resp.status_code
            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_devices(self):
        """
        Get a list of devices
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        resp = self.ise.get('{0}/config/networkdevice'.format(self.url_base))

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        json_res = resp.json()['SearchResult']

        if resp.status_code == 200 and int(json_res['total']) > 1:
            result['success'] = True
            result['response'] = [(i['name'], i['id'])
                                  for i in json_res['resources']]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 1:
            result['success'] = True
            result['response'] = [(json_res['resources'][0]['name'],
                                   json_res['resources'][0]['id'])]
            return result

        elif resp.status_code == 200 and int(json_res['total']) == 0:
            result['success'] = True
            result['response'] = []
            return result

        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def get_device(self, device):
        """
        Get device detailed info
        :param device: User ID
        :return: result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/networkdevice?filter=name.EQ.{1}'.format(self.url_base, device))
        found_device = resp.json()

        if found_device['SearchResult']['total'] == 1:
            resp = self.ise.get('{0}/config/networkdevice/{1}'.format(
                    self.url_base, found_device['SearchResult']['resources'][0]['id']))
            if resp.status_code == 200:
                result['success'] = True
                result['response'] = resp.json()['NetworkDevice']
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(device)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_device['SearchResult']['total'] == 0:
                result['response'] = '{0} not found'.format(device)
                result['error'] = 404
                return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def add_device(self,
                   name,
                   ip_address,
                   radius_key,
                   snmp_ro,
                   dev_group,
                   dev_location,
                   dev_type,
                   description='',
                   snmp_v='TWO_C',
                   dev_profile='Cisco'):
        """
        Add a device
        :param name: name of device
        :param ip_address: IP address of device
        :param radius_key: Radius shared secret
        :param snmp_ro: SNMP read only community string
        :param dev_group: Device group name
        :param dev_location: Device location
        :param dev_type: Device type
        :param description: Device description
        :param dev_profile: Device profile
        :return: Result dictionary
        """
        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})


        data = { 'NetworkDevice' : { 'name': name,
                    'description': description,
                    'authenticationSettings' : {
                        'networkProtocol': 'RADIUS',
                        'radiusSharedSecret': radius_key,
                        'enableKeyWrap' : 'false',
                    },
                    'snmpsettings' : {
                        'version': 'TWO_C',
                        'roCommunity': snmp_ro,
                        'pollingInterval': 3600,
                        'linkTrapQuery': 'true',
                        'macTrapQuery': 'true',
                        'originatingPolicyServicesNode': 'Auto'
                    },
                    'profileName': dev_profile,
                    'coaPort': 1700,
                    'NetworkDeviceIPList': [ {
                        'ipaddress': ip_address,
                        'mask': 32
                    } ],
                    'NetworkDeviceGroupList': [dev_group, dev_type, dev_location, 'IPSEC#Is IPSEC Device#No']
                    }
                }

        resp = self.ise.post('{0}/config/networkdevice'.format(self.url_base), data=json.dumps(data), timeout=self.timeout)

        if resp.status_code == 201:
            result['success'] = True
            result['response'] = '{0} Added Successfully'.format(name)
            return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result

    def delete_device(self, device):
        """
        Delete a device
        :param device: Device ID
        :return: Result dictionary
        """
        self.ise.headers.update({'ACCEPT':'application/json', 'Content-Type':'application/json'})

        result = {
            'success': False,
            'response': '',
            'error': '',
        }

        resp = self.ise.get('{0}/config/networkdevice?filter=name.EQ.{1}'.format(self.url_base, device))
        found_device = resp.json()
        if found_device['SearchResult']['total'] == 1:
            device_oid = found_device['SearchResult']['resources'][0]['id']
            resp = self.ise.delete('{0}/config/networkdevice/{1}'.format(self.url_base, device_oid), timeout=self.timeout)

            if resp.status_code == 204:
                result['success'] = True
                result['response'] = '{0} Deleted Successfully'.format(device)
                return result
            elif resp.status_code == 404:
                result['response'] = '{0} not found'.format(device)
                result['error'] = resp.status_code
                return result
            else:
                result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
                result['error'] = resp.status_code
                return result
        elif found_device['SearchResult']['total'] == 0:
                result['response'] = '{0} not found'.format(device)
                result['error'] = 404
                return result
        else:
            result['response'] = resp.json()['ERSResponse']['messages'][0]['title']
            result['error'] = resp.status_code
            return result
