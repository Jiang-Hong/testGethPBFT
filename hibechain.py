#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from singlechain import SingleChain
from ips import IPList
import threading
import time

class HIBEChain():
    '''
    Data structure for a Hierarchical IBE Chain.
    '''
    def __init__(self, IDList, threshList, IPlist, passwd='Blockchain17'):

        # Check if the input params are legal
        if not len(IDList) == len(threshList):
            raise ValueError("length of IDList should match length of threshList")
        if sum(nodeCount for (nodeCount, _) in threshList) > IPlist.getFullCount():
            raise ValueError("not enough IPs")

        self._chains = []
        self._IDList = IDList
        self._maxLevel = len(IDList[-1])
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
#        threadlist = []
        for index, name in enumerate(IDList):
            level = len(name)
            nodeCount, threshold = threshList[index][0], threshList[index][1]
            blockchainid = 120 + index
            tmp = SingleChain(name, level, nodeCount, threshold, blockchainid, IPlist, passwd)
            if len(name) == self._maxLevel:
                tmp._isTerminal = True
            tmp.SinglechainStart()
            if tmp._isTerminal:
                print(tmp._id, "--------------terminal")
                tmp.TerminalConfig()
            else:
                tmp.SinglechainConfig()
            tmp.runGethNodes()
            tmp.constructChain()
            self._chains.append(tmp)
#            t = threading.Thread(target=tmp.constructChain,args=())
#            t.start()
#            self._chains.append(tmp)
#        for t in threadlist:
#            t.join()

    def constructHIBEChain(self):
        '''
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with their parent blockchain nodes.
        '''
#        threadlist = []
        for chain in self._chains[::-1]:
            if chain.getID() != '':
                parentChain = self._chains[self._IDList.index(chain.getID()[:-1])]
                parentChain.connectLowerChain(chain)
#                print(chain.getID(), parentChain.getID())
                # parentChain.connectLowerChain(chain)
#                t = threading.Thread(target=parentChain.connectLowerChain,args=(chain,))
#                t.start()
#        for t in threadlist:
#            t.join()

    def destructHIBEChain(self):
        '''
        Stop all the nodes in the HIBEChain.
        '''
#        threadlist = []
#        for chain in self._chains:
#            t = threading.Thread(target=chain.destructChain,args=())
#            t.start()
#            threadlist.append(t)
#        for t in threadlist:
#            t.join()
        for chain in self._chains:
            chain.destructChain()

    def getChain(self, ID):
        '''
        Return a list of blockchain nodes with a given ID.
        '''
        try:
            index = self._IDList.index(ID)
            print('index', '-----------', index)
            return self._chains[index]
        except ValueError or IndexError:
            print("ID %s is not in the HIBEChain" % ID)

    def setNumber(self):
        '''
        set (n, t) value for all the chains in HIBEChain.
        '''
#        threadlist = []
#        for chain in self._chains:
#            t = threading.Thread(target = chain.setNumber,args = ())
#            t.start()
#            threadlist.append(t)
#            # chain.setNumber()
#        for t in threadlist:
#            t.join()
#        self._ifSetNumber = True
        for chain in self._chains:
            chain.setNumber()

    def setLevel(self):
        '''
        set level value for all the chains in HIBEChain.
        '''
#        threadlist = []
#        for chain in self._chains:
#            # chain.setLevel(self._maxLevel)
#            t = threading.Thread(target=chain.setLevel,args=(self._maxLevel,))
#            t.start()
#            threadlist.append(t)
#        for t in threadlist:
#            t.join()
#        self._ifSetLevel = True
        for chain in self._chains:
            chain.setLevel(self._maxLevel)

    def setID(self):
        '''
        set ID for all the chains in HIBEChain.
        '''
        if not self._ifSetNumber and self._ifSetLevel:
            raise RuntimeError("number and level info should be set previously")
#        threadlist = []
#        for chain in self._chains:
#            t = threading.Thread(target=chain.setID,args=())
#            t.start()
#            threadlist.append(t)
#        for t in threadlist:
#            t.join()
#        self._ifSetID = True
        for chain in self._chains:
            chain.setID()


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    IDList = ["", "1", "2", "11", "12", "13", "14", "15", "16", "21", "22", "23"]
    threshList = [(10, 8), (6, 5), (6, 5), (1,1), (1,1), (1,1), (1,1), (1,1), (1,1), (1,1), (1,1), (1,1)]
    startTime = time.time()
    hibe = HIBEChain(IDList, threshList, IPlist)
    hibe.constructHIBEChain()

    for chain in hibe._chains:
        for node in chain._nodes:
            print(chain._id, node._id, node.getPeerCount(), node.getPeers())

    hibe.setNumber()
    time.sleep(3)
    hibe.setLevel()
    time.sleep(3)
    hibe.setID()
    endTime = time.time()
    time.sleep(5)

    root, levelOne, personalOne, personalTwo = hibe.getChain(''), hibe.getChain('1'), hibe.getChain('11'), hibe.getChain("12")
    R = root.getPrimer()
    L1 = levelOne.getPrimer()
    P1 = personalOne.getPrimer()
    P2 = personalTwo.getPrimer()
    print(R.getPeerCount(), L1.getPeerCount(), P1.getPeerCount(), P2.getPeerCount()) # 3 5 2 2

#    print(L1.getBalance('0x3131000000000000000000000000000000000001'))
#    print(L1.getBalance('0x3131000000000000000000000000000000000002'))
#    acc = L1.getAccounts()[0]
#    print(acc)
#    print(L1.getBalance(acc))
#    result = P1.sendTransaction('12', 1, 10000)
#    print(result)
#    print(L1.getBalance('0x3131000000000000000000000000000000000001'))
#    print(L1.getBalance('0x3131000000000000000000000000000000000002'))

#    hibe.destructHIBEChain()

    print("HIBEChain construction time:", endTime - startTime)
