#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gethnode import GethNode

class SingleChain():
    '''
    Data structure for a set of Geth-pbft clients for a single blockchain.
    '''

    def __init__(self, name, level, nodeCount, threshold, blockchainid, IPs, rpcPorts, listenerPorts, passwd='Blockchain17'):
        '''
        Setup a set of geth-pbft nodes for one blockchain.
        '''
        assert len(IPs) ==len(rpcPorts) == len(listenerPorts) == nodeCount, "number of nodes doesn't match the number of IPs"
        self._level = level
        self._id = name
        self.nodeCount = nodeCount
        self.threshold = threshold
        self._blockchainid = blockchainid
        self._passwd = passwd
        self._nodes = []
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
        for index, ip in enumerate(IPs):
            pbftid = index
            nodeindex = index + 1
            rpcPort = rpcPorts[index]
            listenerPort = listenerPorts[index]
            tmp = GethNode(ip, pbftid, nodeindex, self._blockchainid, rpcPort, listenerPort, self._passwd)
            self._nodes.append(tmp)

    def getID(self):
        '''
        return ID of the chain.
        '''
        return self._id

    def getPrimer(self):
        '''
        Return the primer node of the set of Geth-pbft clients.
        '''
        return self._nodes[0]
    def getNode(self, nodeindex):
        '''
        Return the node of a given index.
        '''
        assert nodeindex > 0
        return self._nodes[nodeindex]

    def constructChain(self):
        '''
        Construct a single chain.
        '''
        primer = self.getPrimer()
        pEnode = primer.getEnode()
        for node in self._nodes[1:]:
            node.addPeer(pEnode, 0)

    def destructChain(self):
        '''
        Remove all the nodes in the chain.
        '''
        for node in self._nodes:
            node.stop()

    def connectLowerChain(self, otherChain):
        '''
        Connect to a lower single chain.
        '''
        p1 = self.getPrimer()
        p2 = otherChain.getPrimer()
        ep2 = p2.getEnode()
        p1.addPeer(ep2, 1)


    def getNodeCount(self):
        '''
        Return the number of nodes of the blockchain.
        '''
        return len(self._nodes)

    def setNumber(self):
        '''
        Set (number, threshold) value for the nodes of the blockchain.
        '''
        if not self._ifSetNumber:
            p = self.getPrimer()
            p.setNumber(self.nodeCount, self.threshold)
            self._ifSetNumber = True

    def setLevel(self, maxLevel):
        '''
        Set level info for each node.
        '''
        if not self._ifSetLevel:
            for node in self._nodes:
                node.setLevel(self._level, maxLevel)
            self._ifSetLevel = True


    def setID(self):
        '''
        Set ID for the blockchain.
        '''
        assert self._ifSetNumber and self._ifSetLevel and len(self._id) ==  self._level
        if self._level == 0:
            p = self.getPrimer()
            p.setID("")
        else:
            for node in self._nodes:
                node.setID(self._id)
        self._ifSetID = True

