#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

# TODO use config.json or config.xml or config.yaml
# TODO docker_run_command

CONFIG = '../config/conf0.txt'  # config file for HIBEChain
USERNAME = 'root'  # username of servers
PASSWD = 'Blockchain17'  # password of servers
KEY_FILE = '/home/rkd/.ssh/test/id_rsa'
# ssh-copy-id -i private_key_file root@...
# ssh-add /full/path/to/private-key_file
IMAGE = 'rkdghd/geth-pbft:500'  # docker image name
MAXPAYLOAD = 15  # maximum number of containers running on one server
IP_CONFIG = '../config/ip.txt'  # server IPs
SECONDS_IN_A_DAY = 60 * 60 * 24
SEMAPHORE = threading.BoundedSemaphore(5)
