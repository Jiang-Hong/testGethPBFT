#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

CONFIG = 'testLatency2.txt'  # config file for HIBEChain
USERNAME = 'dell'  # username of servers
PASSWD = 'dell@2017'  # password of servers
MAXPAYLOAD = 10  # maximum number of containers running on one server
IP_CONFIG = 'ip.txt'  # server IPs
SECONDS_IN_A_DAY = 60 * 60 * 24
SEMAPHORE = threading.BoundedSemaphore(30)

# wait after copy... for 100 nodes
