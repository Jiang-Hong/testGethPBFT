#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from singlechain import SingleChain

class HIBEChain():
    '''
    Data structure for a Hierarchical IBE Chain.
    '''
    def __init__(self, IDList, threshList, IPList, rpcPortList, listenerPortList, passwd='Blockchain17'):
        assert len(IDList) == len(threshList) == len(IPList) == len(rpcPortList) == len(listenerPortList)
        self._chains = []
        self._IDList = IDList
        self._maxLevel = len(IDList[-1])
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
        for index, name in enumerate(IDList):
            level = len(name)
            nodeCount, threshold = threshList[index][0], threshList[index][1]
            blockchainid = 120 + index
            IPs = IPList[index]
            rpcPorts = rpcPortList[index]
            listenerPorts = listenerPortList[index]
            tmp = SingleChain(name, level, nodeCount, threshold, blockchainid, IPs, rpcPorts, listenerPorts)
            tmp.constructChain()
            self._chains.append(tmp)

    def constructHIBEChain(self):
        '''
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with its parent blockchain nodes.
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

    def setLevel(self):
        '''
        set level value for all the chains in HIBEChain.
        '''
        for chain in self._chains:
            chain.setLevel(self._maxLevel)

    def setID(self):
        '''
        set ID for all the chains in HIBEChain.
        '''
        for chain in self._chains:
            chain.setID()



