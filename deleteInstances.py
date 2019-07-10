# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.DeleteInstanceRequest import DeleteInstanceRequest

from pprint import pprint
import json

from secret import ACCESS_KEY_ID, ACCESS_SECRET

# Describe instances
client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, 'cn-zhangjiakou')

request = DescribeInstancesRequest()
request.set_accept_format('json')

response = client.do_action_with_exception(request)
# print(str(response, encoding='utf-8'))

r = json.loads(str(response, encoding='utf-8'))
instances = (r['Instances']['Instance'])
pprint(instances)
instance_ids = [ins['InstanceId'] for ins in instances]

# Delete Instances
for ins in instance_ids:
    request = DeleteInstanceRequest()
    request.set_accept_format('json')

    request.set_InstanceId(ins)
    request.set_Force(True)

    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))
