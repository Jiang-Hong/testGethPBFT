#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

CONFIG = 'conf1.txt'
USERNAME = 'u0'  # username of servers
PASSWD = 'test'  # password of servers
MAXPAYLOAD = 20  # maximum number of containers running on one server
SEMAPHORE = threading.BoundedSemaphore(10)