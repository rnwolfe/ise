## ISE
Python module to manage Cisco ISE via the REST API.

Thus far, I primarily added the ability to [list large amounts of endpoints in a particular endpoint identity group](#get-a-list-of-all-endpoints-in-an-identity-group). This is so I could dump them into a CSV import template to do easy bulk group moves. The ISE GUI makes it difficult to do exports for endpoints spanning multiple pages (I need to do over 19,000). I may add more stuff in the future.

#### History  
All initial work is done by https://github.com/bobthebutcher, https://github.com/mpenning, and https://github.com/falkowich.  
falkowich forked from them and updated so it worked with ISE 2.2.x and changed all functions to json calls.  

#### Status
Tested and used in our environment at work. But as usual it's up to you to test thus out in a test environment so everything works as intended.

Is you have any suggestions or find a bug, create a issue and I'll try to fix it :)

#### Testing
Testing has been completed on ISE v2.2.0.470 and with python 3.5.2

### Enable REST API
http://www.cisco.com/c/en/us/td/docs/security/ise/2-0/api_ref_guide/api_ref_book/ise_api_ref_ers1.html#pgfId-1079790
Need to add an ISE Administrator with the "ERS-Admin" or "ERS-Operator" group assignment is required to use the API.

### Installation
```bash
mkdir path/to/ise
cd path/to/ise
git clone https://github.com/falkowich/ise.git
```

#### Add to path
```python
import sys
sys.path.append('/path/to/ise/')
```

### Usage
```python
from ise.cream import ERS
ise = ERS(ise_node='192.168.0.10', ers_user='ers', ers_pass='supersecret', verify=False, disable_warnings=True)
```

#### Get a list of all endpoints in an identity group
This was the main reason I forked this repo. I couldn't export more than 500 endpoint in ISE GUI effectively for bulk endpoint group moves, so I made `list_endpoints_in_group()` to do it. It "partially" supports the paginations in the API; however, you have to loop it in your calling of the function. The function will just return if there is a "nextPage" in the API response. Here's my lazy version:

```python
done = 0
page = 1

while done != 1:
	# At this point you need to get the group_id manually using postman or otherwise, will spruce this up in the future. Shouldn't be hard.

	res = ise.list_endpoints_in_group(group_id='7f1012c0-433e-11e3-9c3f-3440b5a29738', page=page)


	for x in res['response']:
		print(x)

	if res['next']:
		#print('more coming')
		page = page + 1
	else:
		done = 1
        
print('Total endpoints: {0}. Pages: {1}'.format( res['total'], page))
```

You can then run it and append output to file: `./list.py >> output.txt`.

This dumps results similar to this which you can easily paste into the endpoint import template: 
```
F4:30:B9:F5:52:19
F4:30:B9:F5:52:7B
F4:30:B9:F5:52:F0
< snipped >
F4:CE:46:46:FE:36
F4:CE:46:47:E5:C8
Total endpoints: 501. Pages: 6
```

#### Methods return a result dictionary
```python
{
    'success': True/False,
    'response': 'Response from request',
    'error': 'Error if any',
}
```

#### Get a list of identity groups
```python
ise.get_identity_groups()['response']

[('NetworkAdmin',
  '5f0b74f0-14e9-11e5-a7a6-00505683258b',
  'Group for Network Admins with CLI access to network equipment'),
 ('OWN_ACCOUNTS (default)',
  'cecdab40-8d30-11e5-82ce-005056834dc2',
  'Default OWN_ACCOUNTS (default) User Group'),
 ('GuestType_Contractor (default)',
  'c9b6b890-8d30-11e5-82ce-005056834dc2',
  'Identity group mirroring the guest type '),
 ...]
```

#### Get details about an identity group
```python
ise.get_identity_group(group='Employee')['response']

{'description': 'Default Employee User Group',
 'id': 'f80e5ce0-f42e-11e2-bd54-005056bf2f0a',
 'link': {'href': 'https://10.8.2.61:9060/ers/config/identitygroup/f80e5ce0-f42e-11e2-bd54-005056bf2f0a',
          'rel': 'self',
          'type': 'application/xml'},
 'name': 'Employee',
 'parent': 'NAC Group:NAC:IdentityGroups:User Identity Groups'}

```

#### Get details about an endpoint
```python
ise.get_endpoint_group(group='Resurs')['response']

 {'description': '',
 'id': 'bf6bdcf0-14ed-11e5-a7a6-00505683258b',
 'link': {'href': 'https://10.8.2.61:9060/ers/config/endpointgroup/bf6bdcf0-14ed-11e5-a7a6-00505683258b',
          'rel': 'self',
          'type': 'application/xml'},
 'name': 'Resurs',
 'systemDefined': False}

```

#### Get endpoint identity groups
```python
ise.get_endpoint_groups()['response']

  [('Cisco-IP-Phone',
    '265079a0-6d8e-11e5-978e-005056bf2f0a',
    'Identity Group for Profile: Cisco-IP-Phone'),
   ('Resurs', '32c8eb40-6d8e-11e5-978e-005056bf2f0a', ''),
   ...]

```

#### Add endpoint
```python
ise.add_endpoint(name='test02', mac='AA:BB:CC:00:11:24', group_id='bf6bdcf0-14ed-11e5-a7a6-00505683258b', description='test02')
{'response': 'test02 Added Successfully', 'success': True, 'error': ''}
```

#### Delete endpoint
```python
ise.delete_endpoint(mac='AA:BB:CC:00:11:27')
{'error': '', 'response': 'AA:BB:CC:00:11:27 Deleted Successfully', 'success': True}

```

#### Get a list of internal users
```python
ise.get_users()['response']

[('test01', '85fd1eb0-c6fa-11e5-b6b6-000c297b78b4'),
 ('test02', '54fd1eb0-c5fb-54e5-b6b6-00204597b28b1'),
 ...]

```

#### Get details about an internal user
```python
ise.get_user(user_id='test02')['response']

{'changePassword': False,
 'customAttributes': {},
 'enablePassword': '*******',
 'enabled': True,
 'expiryDateEnabled': False,
 'id': '54fd1eb0-c5fb-54e5-b6b6-00204597b28b1',
 'identityGroups': '5f0b74f0-14e9-11e5-a7a6-00505683258b',
 'link': {'href': 'https://10.8.2.61:9060/ers/config/internaluser/a837bd55-f2b7-41e3-b0ff-c5ddf9af398c',
          'rel': 'self',
          'type': 'application/xml'},
 'name': 'test02',
 'password': '*******',
 'passwordIDStore': 'Internal Users'}

```

#### Add an internal user
```python
ise.add_user(user_id='test11', password='TeStInG11', user_group_oid='5f0b74f0-14e9-11e5-a7a6-00505683258b')

{'error': '', 'response': 'test11 Added Successfully', 'success': True}

```

#### Delete an internal user
```python
ise.delete_user(user_id='test11')

{'error': '', 'response': 'test11 Deleted Successfully', 'success': True}

```

#### Get a list of devices
```python
ise.get_devices()['response']

[('TestDevice01', '6680f410-5277-11e5-9a52-05505683258b'),
 ('TestDevice02', '64d9b32-5c56-11e5-9a52-00502683258b'),
 ...]

```

#### Get details about a device
```python
ise.get_device(device='TestDevice02')['response']

{'NetworkDeviceGroupList': ['Stage#Stage',
                            'Device Type#All Device Types#Linux',
                            'Location#All Locations'],
 'NetworkDeviceIPList': [{'ipaddress': '10.8.1.55', 'mask': 32}],
 'authenticationSettings': {'enableKeyWrap': False,
                            'keyInputFormat': 'ASCII',
                            'networkProtocol': 'RADIUS',
                            'radiusSharedSecret': '******'},
 'coaPort': 0,
 'id': '74d9b830-5c76-11e5-9a52-00505683258b',
 'link': {'href': 'https://10.8.2.61:9060/ers/config/networkdevice/74d9b830-5c76-11e5-9a52-00505683258b',
          'rel': 'self',
          'type': 'application/xml'},
 'modelName': 'Linux',
 'name': 'TestDevice02',
 'profileName': 'Cisco'}

```

#### Get a list of device groups
```python
ise.get_device_groups()['response']

[('Device Type#All Device Types', '526240e0-f42e-11e2-bd54-005056bf2f0a'),
 ('Device Type#All Device Types#Switch', 'e25bd190-14e6-11e5-a7a6-00505683258b'),
 ('Device Type#All Device Types#Wism', 'e6b085b0-14e6-11e5-a7a6-00505683258b'),
 ('IPSEC#Is IPSEC Device', '0d3f19b0-30c1-11e7-88b5-005056834dc2'),
 ('IPSEC#Is IPSEC Device#No', '0dac0c50-30c1-11e7-88b5-005056834dc2'),
 ('IPSEC#Is IPSEC Device#Yes', '0d74f6c0-30c1-11e7-88b5-005056834dc2'),
 ('Location#All Locations', '522b7970-f42e-11e2-bd54-005056bf2f0a'),
 ...]

```

#### Add a device
```python
ise.add_device(name='testdevice03',
               ip_address='192.168.10.10',
               radius_key='foo',
               snmp_ro='bar',
               dev_group='Stage#Stage#Closed',
               dev_location='Location#All Locations#Site21',
               dev_type='Device Type#All Device Types#Switch')

{'error': '', 'response': 'testdevice03 Added Successfully', 'success': True}

```

#### Delete a device
```python
ise.delete_device(device='testdevice03')

{'error': '', 'response': 'testdevice03 Deleted Successfully', 'success': True}
```
