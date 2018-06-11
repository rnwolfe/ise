# get-endpoints-in-group.py [endpoint-group-name]
# -------------------------------------------------
# Will retrieve all MAC addresses in an endpoint identity group using the group name as the reference.
#-------------------------------------------------
# Recommended: ./get-endpoints-in-group.py [endpoint-group-name] > group-name.txt

import sys
sys.path.append(r'C:\scripts\ise-python')

from ise.cream import ERS

ise = ERS(ise_node='[ise-ip]', ers_user='[ers-admin]', ers_pass='[ers-password]', verify=False, disable_warnings=True)

group_name = sys.argv[1]
group_id   = ise.get_endpoint_group_id(group_name)['response']

done = 0
page = 1

print("Group: {0}, ID: {1}".format( group_name, group_id) )

while done != 1:

	res = ise.list_endpoints_in_group(group_id=group_id, page=page)


	for x in res['response']:
		print(x)

	if res['next']:
		#print('more coming')
		page = page + 1
	else:
		done = 1

print('Total endpoints: {0}. Pages: {1}'.format( res['total'], page))
