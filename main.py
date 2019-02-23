#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hibechain import HIBEChain
from ips import IPList
import time
from gethnode import stopAll, execCommand


IPlist = IPList('ip.txt')
IDList = ["", "0001", "0002"]
threshList = [(4,3), (1, 1), (1, 1)]
#startTime = time.time()
hibe = HIBEChain(IDList, threshList, IPlist)
hibe.constructHIBEChain()

hibe.setNumber()
hibe.setLevel()
hibe.setID()
time.sleep(1)
a = hibe.getChain("")
a1 = a.getNode(1)
print("level 0 keystatus", a1.keyStatus())
b = hibe.getChain("0001")
b1 = b.getNode(1)
print("level 1 keystatus", b1.keyStatus())

hibe.destructHIBEChain()
#endTime = time.time()
#print("HIBEChain construction time:", endTime - startTime)



# docker run -td rkdghd/geth-pbft:latest bash
# docker exec -t b82a7329d31e /usr/bin/geth --datadir abc account new --password passfile