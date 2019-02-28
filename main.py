#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hibechain import HIBEChain
from ips import IPList, startDockerService
import time
from gethnode import stopAll, execCommand


IPlist = IPList('ip.txt')
# startDockerService(IPlist)
IDList = [""]
threshList = [(4, 3)]
for i in range(1, 13):
    index = str(i)
    tmpID = '0' * (4-len(index)) + index
    IDList.append(tmpID)
    threshList.append((1,1))

#IDList = ["", "0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008"]
#threshList = [(4,3), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)]
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
c = hibe.getChain("0002")
c1 = c.getNode(1)
print("level 1 keystatus", c1.keyStatus())



#time.sleep(3)
#b1.testSendTransaction("0001", 1, "0x2", 2, 100)
#time.sleep(1)
#a1.startMiner()

#hibe.destructHIBEChain()
#endTime = time.time()
#print("HIBEChain construction time:", endTime - startTime)



# docker run -td rkdghd/geth-pbft:latest bash
# docker exec -t b82a7329d31e /usr/bin/geth --datadir abc account new --password passfile