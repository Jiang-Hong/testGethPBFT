#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from singlechain import SingleChain
from ips import IPList
import threading

class HIBEChain():
    '''
    Data structure for a Hierarchical IBE Chain.
    '''
    def __init__(self, IDList, threshList, IPlist, passwd='Blockchain17'):

        # Check if the input params are legal
        if not len(IDList) == len(threshList) <=  IPlist.getFullCount():
            raise ValueError("length of IDList should match length of threshList")
        if not sum(nodeCount for (nodeCount, _) in threshList) <= IPlist.getFullCount():
            raise ValueError("not enough IPs")

        self._chains = []
        self._IDList = IDList
        self._maxLevel = len(IDList[-1])
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
        threadlist = []
        for index, name in enumerate(IDList):
            level = len(name)
            nodeCount, threshold = threshList[index][0], threshList[index][1]
            blockchainid = 120 + index
            tmp = SingleChain(name, level, nodeCount, threshold, blockchainid, IPlist, passwd)
            tmp.SinglechainStart()
            t = threading.Thread(target=tmp.constructChain,args=())
            t.start()
            self._chains.append(tmp)
        for t in threadlist:
            t.join()

    def constructHIBEChain(self):
        '''
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with their parent blockchain nodes.
        '''
        for chain in self._chains[::-1]:
            if chain.getID() != '':
                parentChain = self._chains[self._IDList.index(chain.getID()[:-1])]
                parentChain.connectLowerChain(chain)

    def destructHIBEChain(self):
        '''
        Stop all the nodes in the HIBEChain.
        '''
        for chain in self._chains:
            chain.destructChain()

    def getChain(self, ID):
        '''
        Return a list of blockchain nodes with a given ID.
        '''
        try:
            index = self._IDList.index(ID)
            return self._chains[index]
        except ValueError:
            print("ID %s is not in the HIBEChain" % ID)

    def setNumber(self):
        '''
        set (n, t) value for all the chains in HIBEChain.
        '''
        for chain in self._chains:
            chain.setNumber()
        self._ifSetNumber = True

    def setLevel(self):
        '''
        set level value for all the chains in HIBEChain.
        '''
        for chain in self._chains:
            chain.setLevel(self._maxLevel)
        self._ifSetLevel = True

    def setID(self):
        '''
        set ID for all the chains in HIBEChain.
        '''
        if not self._ifSetNumber and self._ifSetLevel:
            raise RuntimeError("number and level info should be set previously")
        for chain in self._chains:
            chain.setID()
        self._ifSetID = True



if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    IDList = ["", "1", "11", "112"]
    threshList = [(2, 2), (2, 2), (3, 2), (2,1)]
    hibe = HIBEChain(IDList, threshList, IPlist)
    hibe.constructHIBEChain()
    a, b, c, d = hibe.getChain(''), hibe.getChain('1'), hibe.getChain('11'), hibe.getChain("112")
    ap1 = a.getPrimer()
    bp1 = b.getPrimer()
    cp1 = c.getPrimer()
    dp1 = d.getPrimer()
    hibe.setNumber()
    hibe.setLevel()
    hibe.setID()
    print(ap1.getPeerCount(), bp1.getPeerCount(), cp1.getPeerCount(), dp1.getPeerCount())
    hibe.destructHIBEChain()
