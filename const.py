#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

ACCESS_KEY_ID = 'LTAIaozu21GFBzmv'
ACCESS_SECRET = 'MddgCoZnG4XZmZaWdJcCB2sZAyFRIe'

CONFIG = 'testLatency1.txt'  # config file for HIBEChain
USERNAME = 'root'  # username of servers
PASSWD = 'Blockchain17'  # password of servers
IMAGE = 'rkdghd/geth-pbft:800'  # docker image name
MAXPAYLOAD = 20  # maximum number of containers running on one server
IP_CONFIG = 'my_ip.txt'  # server IPs
SECONDS_IN_A_DAY = 60 * 60 * 24
SEMAPHORE = threading.BoundedSemaphore(16)
