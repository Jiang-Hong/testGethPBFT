#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

CONFIG = 'config/testLatency3.txt'  # config file for HIBEChain
USERNAME = 'u0'  # username of servers
PASSWD = 'test'  # password of servers
IMAGE = 'rkdghd/geth-pbft:500'  # docker image name
MAXPAYLOAD = 15  # maximum number of containers running on one server
IP_CONFIG = 'config/ip.txt'  # server IPs
SECONDS_IN_A_DAY = 60 * 60 * 24
SEMAPHORE = threading.BoundedSemaphore(6)
