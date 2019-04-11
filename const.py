#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

CONFIG = 'conf0.txt'
USERNAME = 'dell'  # username of servers
PASSWD = 'dell@2017'  # password of servers
MAXPAYLOAD = 15  # maximum number of containers running on one server
SEMAPHORE = threading.BoundedSemaphore(10)