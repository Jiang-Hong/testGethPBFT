#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from singlechain import SingleChain
from iplist import IPList, USERNAME, PASSWD
import threading
import time

class HIBEChain():
    '''
    Data structure for an Hierarchical Identity Based Encryption Chain.
    '''
    def __init__(self, IDList, threshList, IPlist, username=USERNAME, password=PASSWD):
        # Check if the input params are legal
        if not len(IDList) == len(threshList):
            raise ValueError("length of IDList should match length of threshList")
        countNeeded = sum(nodeCount for (nodeCount, _) in threshList)
        countContainers = IPlist.getFullCount()
        if countNeeded > countContainers:
            raise ValueError("%d containers needed but only %d containers available" % (countNeeded, countContainers))

        self._username = username
        self._passwd = password
        self._chains = []
        self._IDList = IDList
        self._threshList = threshList
        self._IPlist = IPlist
        self._maxLevel = len(IDList[-1]) // 4
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
        self._structedChains = []

        self.initChains()

        threads = []
        for level in self._structedChains[:-1]:
            for chain in level:
                t = threading.Thread(target=chain.ConsensusChainConfig, args=())
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        threads = []
#        count = 0
        if not self._structedChains[-1][0]._isTerminal:
            for chain in self._structedChains[-1]:
                t = threading.Thread(target=chain.ConsensusChainConfig, args=())
                t.start()
                threads.append(t)
        else:
            for chain in self._structedChains[-2]:
                chain.LeafChainConfig(self._structedChains[-1])
            for chain in self._structedChains[-1]:
                t = threading.Thread(target=chain.TerminalConfig, args=())
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        time.sleep(2)

        threads = []
#        count = 0
        for chain in self._chains:
#            count += 1
#            if count == 5:
#                count = 0
#                time.sleep(0.5)
#            print("-----geth starting---------")
            t = threading.Thread(target=chain.runNodes, args=())
            t.start()
            threads.append(t)
            time.sleep(1)
        for t in threads:
            t.join()

    def constructHIBEChain(self):
        '''
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with their parent blockchain nodes.
        '''
        print('construct hibechain')
        threadlist = []
#        count = 0
        for chain in self._chains[::-1]:
#            count += 1
#            if count == 2:
#                time.sleep(0.5)
#                count = 0
#                print("construct HIBEChain wait here...")
            if chain.getID() != '':
                parentChain = self._chains[self._IDList.index(chain.getID()[:-4])]
#                parentChain.connectLowerChain(chain)
                t = threading.Thread(target=parentChain.connectLowerChain,args=(chain, ))
                t.start()
                threadlist.append(t)
                time.sleep(1)
                print('active threads:', threading.active_count())
        for t in threadlist:
            t.join()
        time.sleep(2)

    def destructHIBEChain(self):
        '''Stop all containers to destruct the HIBEChain.'''
        threadlist = []
        for chain in self._chains:
            t = threading.Thread(target=chain.destructChain,args=())
            t.start()
            threadlist.append(t)
            time.sleep(0.1)
        for t in threadlist:
            t.join()

    def getChain(self, ID):
        '''Return a list of blockchain nodes with a given chain ID(eg. '00010001').'''
        try:
            index = self._IDList.index(ID)
            return self._chains[index]
        except ValueError or IndexError:
            print("ID %s is not in the HIBEChain" % ID)

    def getParentChain(self, chain):
        '''
        Return parent chain.
        Return None if current chain is root chain.
        '''
        if chain._id == '':
            print('root chain does not have a parent chain')
            return None
        else:
            parentID = chain._id[:-4]
            return self.getChain(parentID)

    def isRootChain(self, chain):
        '''Check if chain is root chain.'''
        return chain._id == ''

    def initChains(self):
        threadlist = []
        # count = 0
        level = 0
        tmpChain = []
        for index, name in enumerate(self._IDList):
            if name:
                print("name is %s" % name, end=" ")
            else:
                print("name is blank", end=" ")
            currentLevel = len(name) // 4
            nodeCount, threshold = self._threshList[index][0], self._threshList[index][1]
            blockchainid = 120 + index
            tmp = SingleChain(name, currentLevel, nodeCount, threshold, blockchainid, self._IPlist, self._username, self._passwd)
            self._chains.append(tmp)
            if currentLevel == level:
                tmpChain.append(tmp)
            else:
                self._structedChains.append(tmpChain)
                tmpChain = []
                tmpChain.append(tmp)
                level = currentLevel
            # count += 1
            # if count == 5:
            #     time.sleep(0.8)
            #     count = 0
            t = threading.Thread(target=tmp.SinglechainStart, args=())
            t.start()
            threadlist.append(t)
            time.sleep(0.1)
        self._structedChains.append(tmpChain)

        print()

        for t in threadlist:
            t.join()
        for ch in self._structedChains[-1]:
            if ch.threshold == 1:
                ch._isTerminal = True

    def setNumber(self):
        '''Set (n, t) value for all chains in HIBEChain.'''
        threadlist = []
        for chain in self._chains:
            t = threading.Thread(target = chain.setNumber,args = ())
            t.start()
            threadlist.append(t)
        for t in threadlist:
            t.join()
        self._ifSetNumber = True
        time.sleep(1)

    def setLevel(self):
        '''Set level value for all chains in HIBEChain.'''

        threadlist = []
        for chain in self._chains:
            t = threading.Thread(target=chain.setLevel,args=(self._maxLevel,))
            t.start()
            threadlist.append(t)
        print('waiting for set level')
        for t in threadlist:
            print('.', end='')
            t.join()
        self._ifSetLevel = True
        time.sleep(1)

    def setID(self):
        '''Set ID for all chains in HIBEChain.'''

        if not self._ifSetNumber and self._ifSetLevel:
            raise RuntimeError("number and level info should be set previously")
        startTime = time.time()
        threads = []
        # count = 0
        for n, level in enumerate(self._structedChains):
            for chain in level:
                # count += 1
                # if count == 5:
                #     count = 0
                #     time.sleep(0.5)
                t = threading.Thread(target=chain.setID, args=())
                t.start()
                threads.append(t)
                time.sleep(0.1)
            for t in threads:
                t.join()

            print('waiting for delivering key')
            if n == 0:
                sleepTime = max([chain.nodeCount for chain in level]) * 10
                print('root level waiting...%ds' % sleepTime)
                time.sleep(sleepTime)
                while not all([node.keyStatus() for node in chain._nodes for chain in level]):
                    print('root level waiting...')
                    time.sleep(5)
                time.sleep(5)


            else:
#                thresh = max((chain.threshold for chain in level))
                while not all([node.keyStatus() for node in chain._nodes for chain in level]):
                    print('.', end='')
                    time.sleep(2)
                time.sleep(2)
        self._ifSetID = True
        print("------setID finished----------------")
        endTime = time.time()
        print('setID elapsed time %.2f' % (endTime - startTime))

    def startMiner(self):
        '''Start miner for all consensus nodes.'''

        for level in self._structedChains[:-1]:
            for chain in level:
                chain.startMiner()


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    IDList = ["", "0001", "0002"]
    threshList = [(4,3), (1, 1), (1, 1)]

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

