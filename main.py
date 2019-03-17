#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hibechain import HIBEChain
from ips import IPList, startDockerService, stopAllContainers, execCommand
from conf import loadCfg
import time
import threading

#threading.stack_size(100*1024*1024)
#TODO remove addPeer sleep time
#TODO IP class with more function. use IP class in other module
#TODO rewrite rpc message with decorator
#TODO function annotation
#TODO connection  peer reset -- set ClientAliveInterval ClientAliveCountMax TCPKeepAlive -- sshd_config all params

failCount = 0

def checkKeyStatus(node):
    if node.keyStatus() is not True:
        print("keyStatus of node at %s:%s is False" % (node._ip, node._listenerPort))
        print("node peer count is %s" % node.getPeerCount())
        global failCount
        failCount += 1

IPlist = IPList('ip.txt')

IDList, threshList = loadCfg(cfgFile='conf.txt')

#nodeCount = 20
#IDList = ['']
#threshList = [(4, 3)]
#for i in range(1, nodeCount-3):
#    index = str(i)
#    tmpID = '0' * (4-len(index)) + index
#    IDList.append(tmpID)
#    threshList.append((1,1))
#nodeCount = sum(nodeCount for (nodeCount, _) in threshList)

print(IDList)
print(threshList)

startTime = time.time()
hibe = HIBEChain(IDList, threshList, IPlist)
hibe.constructHIBEChain()

connectionTime = time.time()
print("connect time", connectionTime-startTime)


a = hibe.getChain("")
a1 = a.getNode(1)

#print('waiting for addPeer')
#count = 0
#while a1.getPeerCount() <= nodeCount-nodeCount//10:
#    print(a1.getPeerCount(), '.', end='')
#    count += 1
#    if count >= 20:
#        break
#    time.sleep(0.5)

print('another %s seconds waiting for addPeer' % str(10))
time.sleep(10)
print('peer count of a1----', a1.getPeerCount())

hibe.setNumber()
hibe.setLevel()
hibe.setID()

endTime = time.time()

#print("level 0 keystatus", a1.keyStatus())
b = hibe.getChain("0001")
b1 = b.getNode(1)
#print("level 1 keystatus", b1.keyStatus())
#c = hibe.getChain("0002")
#c1 = c.getNode(1)z
#print("level 1 keystatus", c1.keyStatus())


threads = []
count = 0
for chain in hibe._chains[1:]:
    for node in chain._nodes:
        count += 1
        if count == 5:
            time.sleep(0.5)
            count = 0
        t = threading.Thread(target=checkKeyStatus, args=(node,))
        t.start()
        threads.append(t)
#        print(node.getPeerCount())
for t in threads:
    t.join()

'''

threads = []
count = 0
for chain in hibe._chains[1:]:
    print("chain id", chain._id)
    count += 1
    if count == 10:
        time.sleep(0.3)
        count = 0
    tmpNode = chain.getNode(1)
    t = threading.Thread(target=tmpNode.testSendTransaction, args=("0001", 1, "0x1", 1, 250))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

#for chain in hibe._chains[1:]:
#    print("chain id", chain._id)
#    tmpNode = chain.getNode(1)
#    tmpNode.testSendTransaction("0001", 1, "0x1", 1, 250)


time.sleep(3)
a1.txpoolStatus()

threads = []
for rootNode in a._nodes:
    t = threading.Thread(target=rootNode.startMiner, args=())
#    rootNode.startMiner()
    t.start()
    threads.append(t)
for t in threads:
    t.join()

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

time.sleep(10)
count = 0
for chain in hibe._chains:
    for node in chain._nodes:
        print(node.getPeerCount(), end=" ")
        count += 1
    if count >= 20:
        break


for i in range(1, 20):
    print(a1.getBlockTransactionCount(i))

print("----------------------------------------------------------------")
print("node count", nodeCount)
print("connection time", connectionTime - startTime)
print("total elapsed time:", endTime - startTime)
'''
print("failCount", failCount)
'''
print(time.ctime())
print("----------------------------------------------------------------")



#a1.getBlockTransactionCount(1)

#time.sleep(3)
#b1.testSendTransaction("0001", 1, "0x2", 2, 100)
#time.sleep(1)
#a1.startMiner()

#hibe.destructHIBEChain()

'''




# docker run -td rkdghd/geth-pbft:latest bash
# docker exec -t b82a7329d31e /usr/bin/geth --datadir abc account new --password passfile