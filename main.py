#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hibechain import HIBEChain
from ips import IPList, startDockerService, stopAllContainers
import time
import threading
from gethnode import stopAll, execCommand

failCount = 0

def checkKeyStatus(node):
    if node.keyStatus() is False:
        print("keyStatus of node at %s:%s is False" % (node._ip, node._listenerPort))
        print("node peer count is %s" % node.getPeerCount())
        global failCount
        failCount += 1

nodeCount = 60

IPlist = IPList('ip.txt')
# startDockerService(IPlist)
IDList = [""]
threshList = [(4, 3)]
for i in range(1, nodeCount-3):
    index = str(i)
    tmpID = '0' * (4-len(index)) + index
    IDList.append(tmpID)
    threshList.append((1,1))

#IDList = ["", "0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008"]
#threshList = [(4,3), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)]
startTime = time.time()
hibe = HIBEChain(IDList, threshList, IPlist)
hibe.constructHIBEChain()

a = hibe.getChain("")
a1 = a.getNode(1)

print('waiting for addPeer')
count = 0
while a1.getPeerCount() <= nodeCount-nodeCount//10:
    print(a1.getPeerCount(), '.', end='')
    count += 1
    if count >= 20:
        break
    time.sleep(0.5)

print('another %s seconds waiting for addPeer' % str(nodeCount//50+5))
time.sleep(nodeCount//50+5)

hibe.setNumber()
hibe.setLevel()
hibe.setID()

endTime = time.time()

#print("level 0 keystatus", a1.keyStatus())
b = hibe.getChain("0001")
b1 = b.getNode(1)
#print("level 1 keystatus", b1.keyStatus())
c = hibe.getChain("0002")
c1 = c.getNode(1)
#print("level 1 keystatus", c1.keyStatus())

threads = []
for chain in hibe._chains[1:]:
    tmpNode = chain.getNode(1)
    t = threading.Thread(target=tmpNode.testSendTransaction, args=("0001", 1, "0x1", 3, 100))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

threads = []
for chain in hibe._chains[1:]:
    for node in chain._nodes:
        t = threading.Thread(target=checkKeyStatus, args=(node,))
        t.start()
        threads.append(t)
#        print(node.getPeerCount())
for t in threads:
    t.join()

for rootNode in a._nodes:
    rootNode.startMiner()

#threadList = []
#for chainID in IDList[1:]:
#    tmpChain = hibe.getChain(chainID)
#    print(chainID, end="-")
#    tmpNode = tmpChain.getNode(1)
#    t = threading.Thread(target=tmpNode.testSendTransaction, args=("0001",1,'0x1',1,100))
#    t.start()
#    threadList.append(t)
#for t in threadList:
#    t.join()

print("elapsed time:", endTime - startTime)
print("failCount", failCount)

#a1.getBlockTransactionCount(1)

#time.sleep(3)
#b1.testSendTransaction("0001", 1, "0x2", 2, 100)
#time.sleep(1)
#a1.startMiner()

#hibe.destructHIBEChain()






# docker run -td rkdghd/geth-pbft:latest bash
# docker exec -t b82a7329d31e /usr/bin/geth --datadir abc account new --password passfile