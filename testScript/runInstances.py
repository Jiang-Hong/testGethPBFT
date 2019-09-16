# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import datetime
import traceback

from src.secret import ACCESS_KEY_ID, ACCESS_SECRET

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest

RUNNING_STATUS = 'Running'
CHECK_INTERVAL = 3
CHECK_TIMEOUT = 180


class AliyunRunInstances(object):

    def __init__(self, aliyun_region, image_id, instance_type, instance_amount,
                 auto_release_time, instance_name, is_dry_run=True):
        self.access_id = ACCESS_KEY_ID
        self.access_secret = ACCESS_SECRET

        # 是否只预检此次请求。true：发送检查请求，不会创建实例，也不会产生费用；false：发送正常请求，通过检查后直接创建实例，并直接产生费用
        self.dry_run = is_dry_run
        # 实例所属的地域ID
        self.region_id = aliyun_region
        # 实例的资源规格
        self.instance_type = instance_type
        # 实例的计费方式
        self.instance_charge_type = 'PostPaid'
        # 指定创建ECS实例的数量
        self.amount = instance_amount
        # 购买资源的时长单位
        self.period_unit = 'Hourly'
        # 自动释放时间 （UTC 时间）
        self.auto_release_time = auto_release_time
        # 镜像ID
        self.image_id = image_id
        # 指定新创建实例所属于的安全组ID
        self.security_group_id = 'sg-8vbcmij3wtpiz6la5fxo'
        # 购买资源的时长
        self.period = 1
        # 实例所属的可用区编号
        self.zone_id = 'random'
        # 网络计费类型
        self.internet_charge_type = 'PayByTraffic'
        # 虚拟交换机ID
        self.vswitch_id = 'vsw-8vb1lonrynma16k3e7wge'
        # 实例名称
        self.instance_name = instance_name
        # 实例的描述
        self.description = 'geth-pbft'
        # 是否使用镜像预设的密码
        self.password_inherit = True
        # 公网出带宽最大值
        self.internet_max_bandwidth_out = 5
        # 云服务器的主机名
        self.host_name = 'test'
        # 是否为实例名称和主机名添加有序后缀
        self.unique_suffix = True
        # 是否为I/O优化实例
        self.io_optimized = 'optimized'
        # 系统盘大小
        self.system_disk_size = '40'
        # 系统盘的磁盘种类
        self.system_disk_category = 'cloud_efficiency'

        self.client = AcsClient(self.access_id, self.access_secret, self.region_id)

    def run(self):
        try:
            ids = self.run_instances()
            self._check_instances_status(ids)
        except ClientException as e:
            print('Fail. Something with your connection with Aliyun go incorrect.'
                  ' Code: {code}, Message: {msg}'
                  .format(code=e.error_code, msg=e.message))
        except ServerException as e:
            print('Fail. Business error.'
                  ' Code: {code}, Message: {msg}'
                  .format(code=e.error_code, msg=e.message))
        except Exception:
            print('Unhandled error')
            print(traceback.format_exc())

    def run_instances(self):
        """
        调用创建实例的API，得到实例ID后继续查询实例状态
        :return:instance_ids 需要检查的实例ID
        """
        request = RunInstancesRequest()

        request.set_DryRun(self.dry_run)

        request.set_InstanceType(self.instance_type)
        request.set_InstanceChargeType(self.instance_charge_type)
        request.set_ImageId(self.image_id)
        request.set_SecurityGroupId(self.security_group_id)
        request.set_Period(self.period)
        request.set_PeriodUnit(self.period_unit)
        request.set_ZoneId(self.zone_id)
        request.set_InternetChargeType(self.internet_charge_type)
        request.set_VSwitchId(self.vswitch_id)
        request.set_InstanceName(self.instance_name)
        request.set_Description(self.description)
        request.set_PasswordInherit(self.password_inherit)
        request.set_Amount(self.amount)
        request.set_InternetMaxBandwidthOut(self.internet_max_bandwidth_out)
        request.set_HostName(self.host_name)
        request.set_UniqueSuffix(self.unique_suffix)
        request.set_IoOptimized(self.io_optimized)
        request.set_AutoReleaseTime(self.auto_release_time)
        request.set_SystemDiskSize(self.system_disk_size)
        request.set_SystemDiskCategory(self.system_disk_category)

        body = self.client.do_action_with_exception(request)
        data = json.loads(body)
        instance_ids = data['InstanceIdSets']['InstanceIdSet']
        print('Success. Instance creation succeed. InstanceIds: {}'.format(', '.join(instance_ids)))
        return instance_ids

    def _check_instances_status(self, instance_ids):
        """
        每3秒中检查一次实例的状态，超时时间设为3分钟.
        :param instance_ids 需要检查的实例ID
        :return:
        """
        start = time.time()
        while True:
            request = DescribeInstancesRequest()
            request.set_InstanceIds(json.dumps(instance_ids))
            body = self.client.do_action_with_exception(request)
            data = json.loads(body)
            for instance in data['Instances']['Instance']:
                if RUNNING_STATUS in instance['Status']:
                    instance_ids.remove(instance['InstanceId'])
                    print('Instance boot successfully: {}'.format(instance['InstanceId']))

            if not instance_ids:
                print('Instances all boot successfully')
                break

            if time.time() - start > CHECK_TIMEOUT:
                print('Instances boot failed within {timeout}s: {ids}'
                      .format(timeout=CHECK_TIMEOUT, ids=', '.join(instance_ids)))
                break

            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    """
    需要修改的变量：
    ACCESS_KEY_ID, ACCESS_SECRET
    image_id: 镜像id
    is_dry_run: 只有设置为 False 才能真正购买服务器，可以设置为 True 来再次获得 ip 列表，建议购买服务器后立即设置为 True
    instance_type: 实例类型
    instance_amount: 实例数量q
    ordered_hours: 购买小时数
    instance_name: 按需修改
    instances: 确认 AliyunRunInstances 实例化的参数
    client: 确认服务器地址信息
    request.set_InstanceName('name'): 跟 instance_name 一致
    with open('ip_list_name', 'w') as ip_file: 按需修改
    """

    # set parameters for instances
    aliyun_region_id = {1: 'cn-zhangjiakou', 2: 'cn-beijing', 3: 'cn-hangzhou', 4: 'cn-shanghai', 5: 'cn-shenzhen',
                        6: 'cn-qingdao', 7: 'cn-huhehaote'}
    image_id = 'm-8vb3i5iaiyul8xshx9w3'

    # keep this variable True in case of mis-operation
    is_dry_run = True  # change this variable to False to run instances in effect
    instance_type = 'ecs.r6.xlarge'  # change this value to instance type you need
    instance_amount = 1

    ordered_hours = 2  # generate auto release time according to ordered hours
    time_now_utc = datetime.datetime.utcnow()
    release_time = time_now_utc + datetime.timedelta(hours=ordered_hours)
    auto_release_time = release_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    instance_name = 'geth-pbft-%s' % time_now_utc.strftime('%Y%m%dT%H%M%S')
    instances = AliyunRunInstances(aliyun_region_id[1], image_id, instance_type, instance_amount,
                                   auto_release_time, instance_name, is_dry_run)
    instances.run()

    print('waiting...')
    time.sleep(20)
    # ------------------------------------------------------------------
    # write IP addresses of instances to file
    client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, 'cn-zhangjiakou')
    request = DescribeInstancesRequest()
    request.set_accept_format('json')
    request.set_PageSize(100)
    request.set_InstanceName("geth-pbft*")
    response = client.do_action_with_exception(request)

    r = json.loads(str(response, encoding='utf-8'))
    instances = (r['Instances']['Instance'])
    ips = [ins['PublicIpAddress']['IpAddress'][0] + '\n' for ins in instances]
    print(len(ips), ips)
    with open('../config/my_ip.txt', 'w') as ip_file:
        ip_file.writelines(ips)

