#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gethnode import GethNode
from ips import IPList
import threading

class SingleChain():
    '''
    Data structure for a set of Geth-pbft clients for a single blockchain.
    '''

    def __init__(self, name, level, nodeCount, threshold, blockchainid, IPlist, passwd='Blockchain17'):
        '''
        init a set of geth-pbft nodes for one blockchain.
        '''
        self._level = level
        self._id = name
        self.nodeCount = nodeCount
        self.threshold = threshold
        self._blockchainid = blockchainid
        self._iplist = IPlist
        self._passwd = passwd
        self._nodes = []
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
    def SinglechainStart(self):
        '''
        run a singlechain
        '''
        threadlist = []
        for index in range(self.nodeCount):
            pbftid = index
            nodeindex = index + 1
            tmp = GethNode(self._iplist, pbftid, nodeindex, self._blockchainid, self._passwd)
            # xq start a thread， target stand for a function that you want to run ,args stand for the parameters
            t = threading.Thread(target=tmp.start)
            threadlist.append(t)
            self._nodes.append(tmp)
            t.start()

        for t in threadlist:
            # xq threads must run the join function ,because the resources of main thread is needed
            t.join()

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
        if nodeindex <= 0 or nodeindex > len(self._nodes):
            raise ValueError("nodeindex out of range")
        return self._nodes[nodeindex-1]

    def constructChain(self):
        '''
        Construct a single chain.
        '''
        primer = self.getPrimer()
        pEnode = primer.Enode

        # add peer for each node
        threadlist = []
        for node in self._nodes[1:]:
            t = threading.Thread(target=node.addPeer,args=(pEnode,0))
            t.start()
            threadlist.append(t)
        for t in threadlist:
            t.join()

    def destructChain(self):
        '''
        Remove all the nodes in the chain.
        '''
        threadlist = []
        for node in self._nodes:
            t = threading.Thread(target=node.stop,args=())
            t.start()
            threadlist.append(t)
        for t in threadlist:
            t.join()

    def connectLowerChain(self, otherChain):
        '''
        Connect to a lower single chain.
        '''
        p1 = self.getPrimer()
        p2 = otherChain.getPrimer()
        ep2 = p2.Enode
        p1.addPeer(ep2, 1)

    def connectUpperChain(self, otherChain):
        '''
        Connect to an upper single chain.
        '''
        p1 = self.getPrimer()
        p2 = otherChain.getPrimer()
        ep2 = p2.Enode
        p1.addPeer(ep2, 2)


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
        else:
            raise RuntimeError("number of chain %s already set" % self._id)

    def setLevel(self, maxLevel):
        '''
        Set level info for each node.
        '''
        if not self._ifSetLevel:
            for node in self._nodes:      #TODO
                node.setLevel(self._level, maxLevel)
            self._ifSetLevel = True
        else:
            raise RuntimeError("level of chain %s already set" % self._id)


    def setID(self):  #TODO
        '''
        Set ID for the blockchain.
        '''
        if not self._ifSetNumber and self._ifSetLevel:
            raise RuntimeError("number and level info should be set previously")
        if len(self._id) != self._level:
            raise ValueError("length of id should match level number")
        if not self._ifSetID:
            if self._level == 0:
                p = self.getPrimer()
                p.setID("")
            else:
                for node in self._nodes:   #TODO
                    node.setID(self._id)
            self._ifSetID = True
        else:
            raise RuntimeError("ID of chain %s already set" % self._id)


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    c = SingleChain('1', 1, 7, 5, 121, IPlist)
    c.SinglechainStart()
    c.constructChain()
    p = c.getPrimer()
    print(p.getPeerCount())
    c.destructChain()
