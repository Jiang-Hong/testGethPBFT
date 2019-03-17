#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from singlechain import SingleChain
from ips import IPList, execCommand, stopAll, USERNAME, PASSWD
import threading
import time
from math import sqrt

class HIBEChain():
    '''
    Data structure for a Hierarchical IBE Chain.
    '''
    def __init__(self, IDList, threshList, IPlist, username=USERNAME, password=PASSWD):

        # Check if the input params are legal
        if not len(IDList) == len(threshList):
            raise ValueError("length of IDList should match length of threshList")
        countNeeded = sum(nodeCount for (nodeCount, _) in threshList)
        countContainers = IPlist.getFullCount()
        if countNeeded > countContainers:
            raise ValueError("not enough IPs. %d containers needed but only %d containers available" % (countNeeded, countContainers))

        self._username = username
        self._passwd = password
        self._chains = []
        self._IDList = IDList
        self._maxLevel = len(IDList[-1]) // 4
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False

        threadlist = []
        count = 0
        for index, name in enumerate(IDList):
            level = len(name) // 4
            if name:
                print("name is %s" % name, end=" ")
            else:
                print("name is blank", end=" ")
            nodeCount, threshold = threshList[index][0], threshList[index][1]
            blockchainid = 120 + index
            tmp = SingleChain(name, level, nodeCount, threshold, blockchainid, IPlist, self._username, self._passwd)
            if level == self._maxLevel and tmp.threshold == 1:
                print("Terminal: name", name, "maxlevel", self._maxLevel)
                tmp._isTerminal = True

#            tmp.SinglechainStart()
            self._chains.append(tmp)
            count += 1
            if count == 5:
                time.sleep(0.8)
                count = 0
            t = threading.Thread(target=tmp.SinglechainStart, args=())
            t.start()
            threadlist.append(t)

        for t in threadlist:
            t.join()

        threads = []
        count = 0
        for chain in self._chains:
            count += 1
            if not chain._isTerminal:
                t = threading.Thread(target=chain.ConsensusChainConfig, args=())
            else:
                if count >= 5:
                    time.sleep(0.8)
                    print("config terminal.................................................")
                    count = 0
#                print(chain._id, "-------------terminal")
                t = threading.Thread(target=chain.TerminalConfig, args=())
            t.start()
            threads.append(t)

        for t in threads:
            print('...', end='')
            t.join()
        print("................config terminal finished")


#            if not tmp._isTerminal:
#                tmp.ConsensusChainConfig()
#            else:
#                print(tmp._id, "--------------terminal")
#                tmp.TerminalConfig()
#            self._chains.append(tmp)

#            t = threading.Thread(target=tmp.constructChain,args=())
#            t.start()
#            self._chains.append(tmp)
#        for t in threadlist:
#            t.join()

        threads = []
        count = 0
        for chain in self._chains:
            count += 1
            if count == 5:
                time.sleep(0.5)
                print("-----geth starting--------------------------")
                count = 0
            t = threading.Thread(target=chain.runNodes, args=())
            t.start()
            threads.append(t)

#            chain.runNodes()
        for t in threads:
            t.join()

        time.sleep(2)

    def constructHIBEChain(self):
        '''
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with their parent blockchain nodes.
        '''
        threadlist = []
        count = 0
        for chain in self._chains[::-1]:
            count += 1
            if count == 5:
                time.sleep(0.5)
                count = 0
                print("construct HIBEChain wait here.................................................")
            if chain.getID() != '':
                parentChain = self._chains[self._IDList.index(chain.getID()[:-4])]
#                parentChain.connectLowerChain(chain)
#                print(chain.getID(), parentChain.getID())
                # parentChain.connectLowerChain(chain)
                t = threading.Thread(target=parentChain.connectLowerChain,args=(chain, ))
                t.start()
        for t in threadlist:
            t.join()
        time.sleep(3)

    def destructHIBEChain(self):
        '''
        Stop all the nodes in the HIBEChain.
        '''
        threadlist = []
        for chain in self._chains:
            t = threading.Thread(target=chain.destructChain,args=())
            t.start()
            threadlist.append(t)
        for t in threadlist:
            t.join()
#        for chain in self._chains:
#            chain.destructChain()

    def getChain(self, ID):
        '''
        Return a list of blockchain nodes with a given ID.
        '''
        try:
            index = self._IDList.index(ID)
#            print('chain index', '-----------', index)
            return self._chains[index]
        except ValueError or IndexError:
            print("ID %s is not in the HIBEChain" % ID)

    def setNumber(self):
        '''
        set (n, t) value for all the chains in HIBEChain.
        '''
        threadlist = []
        count = 0
        for chain in self._chains:
            count += 1
            if count == 10:
                time.sleep(0.5)
                count = 0
            t = threading.Thread(target = chain.setNumber,args = ())
            t.start()
            threadlist.append(t)
#            # chain.setNumber()
        for t in threadlist:
            t.join()
        self._ifSetNumber = True
        time.sleep(1)
#        for chain in self._chains:
#            chain.setNumber()

    def setLevel(self):
        '''
        set level value for all the chains in HIBEChain.
        '''
        threadlist = []
        count = 0
        for chain in self._chains:
            # chain.setLevel(self._maxLevel)
            count += 1
            if count == 10:
                time.sleep(0.5)
                count = 0
            t = threading.Thread(target=chain.setLevel,args=(self._maxLevel,))
            t.start()
            threadlist.append(t)
        print('waiting for set level')
        for t in threadlist:
            print('...', end='')
            t.join()
        self._ifSetLevel = True
        time.sleep(1)
#        for chain in self._chains:
#            chain.setLevel(self._maxLevel)

    def setID(self):
        '''
        set ID for all the chains in HIBEChain.
        '''
        if not self._ifSetNumber and self._ifSetLevel:
            raise RuntimeError("number and level info should be set previously")
        idLength = 0
        chains = []
        tmp = []
        for chain in self._chains:
            if len(chain._id) == idLength:
                tmp.append(chain)
            elif len(chain._id) != idLength:
                chains.append(tmp)
                tmp = []
                tmp.append(chain)
                idLength = len(chain._id)
        chains.append(tmp)

#        print("--------------------------------------------")
#        for i in chains:
#            print(len(i))
#        print("--------------------------------------------")

        threads = []
        count = 0
        for n, level in enumerate(chains):
            for chain in level:
                count += 1
                if count == 5:
                    time.sleep(1)
                    count = 0
                t = threading.Thread(target=chain.setID, args=())
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

            baseCount = max([chain.threshold for chain in level]) + 1
            sleepTime = 5 * baseCount
            print("-----waiting for setID---------%d--%ds" % (n, sleepTime))
            time.sleep(sleepTime)
        self._ifSetID = True
#        level = len(self._IDList[-1]) // 4
#        print("level is %d", level)
#        for i in range(level):
#            time.sleep(15)
        print("------setID finished----------------")


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    # startDockerService(IPlist)
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

