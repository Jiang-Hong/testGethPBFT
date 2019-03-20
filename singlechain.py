#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gethnode import GethNode
from ips import IPList, USERNAME, PASSWD
import threading
from conf import confGenesis
import time
import subprocess
import requests
import json
from functools import wraps

class SingleChain():
    '''
    Data structure for a set of Geth-pbft clients for a single blockchain.
    '''

    def __init__(self, name, level, nodeCount, threshold, blockchainid, IPlist, username=USERNAME, passwd=PASSWD):
        '''
        init a set of geth-pbft nodes for one blockchain.
        '''
        if nodeCount > IPlist.getFullCount():
            raise ValueError("not enough IPs")

        self._username = username
        self._passwd = passwd
        self._level = level
        self._id = name
        self.nodeCount = nodeCount
        self.threshold = threshold
        self._blockchainid = blockchainid
        self._IPlist = IPlist
        self._nodes = []
        self._IPs = set()
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
        self._isTerminal = False
        self._cfgFile = None
        self._accounts = []

    def SinglechainStart(self):
        '''
        run a singlechain
        '''
        threadlist = []
        for index in range(self.nodeCount):
            pbftid = index
            nodeindex = index + 1
            tmp = GethNode(self._IPlist, pbftid, nodeindex, self._blockchainid, self._username, self._passwd)
            self._IPs.add(tmp._IP)
            self._nodes.append(tmp)
            # xq start a thread， target stand for a function that you want to run ,args stand for the parameters
            t = threading.Thread(target=tmp.start)
            t.start()
            threadlist.append(t)

        for t in threadlist:
            # xq threads must run the join function, because the resources of main thread is needed
            t.join()

        for index in range(self.nodeCount):
            self._accounts.append(self._nodes[index]._accounts[0])
#        print(self._accounts)

    def _setGenesisDecorator(config):
        '''
        Decorator for setting genesis.json file for a chain.
        '''
        @wraps(config)
        def func(self):
            config(self)
            for serverIP in self._IPs:
                subprocess.run(['sshpass -p %s scp docker/%s %s@%s:%s' % (self._passwd, self._cfgFile, self._username, serverIP._ipaddr, self._cfgFile) ], stdout=subprocess.PIPE, shell=True)
                time.sleep(0.5)
                threads = []
                for node in self._nodes:
                    if node._IP == serverIP:
                        CMD = 'docker cp %s %s:/root/%s' % (self._cfgFile, node._name, self._cfgFile)
                        t = threading.Thread(target=serverIP.execCommand, args=(CMD,))
                        t.start()
                        threads.append(t)
                for t in threads:
                    t.join()
                time.sleep(0.2)
        return func

    @_setGenesisDecorator
    def ConsensusChainConfig(self):
        '''
        set genesis.json for a blockchain & init with genesis.json
        '''
        if self._id is "":
            self._cfgFile = '0.json'
        else:
            self._cfgFile = '%s.json' % self._id
        confGenesis(self._blockchainid, self._accounts, self._cfgFile)

    @_setGenesisDecorator
    def TerminalConfig(self):
        '''
        set genesis.json for terminal equipments.
        '''
        if len(self._id) == 4:
            self._cfgFile = '0.json'
        else:
            self._cfgFile = '%s.json' % self._id[:-4]

    def runNodes(self):
        '''
        Run nodes on a chain.
        '''
        self.gethInit()
        self.runGethNodes()
        self.constructChain()

    def gethInit(self):
        '''
        run geth init command for nodes in a chain
        '''
        if self._cfgFile is None:
            raise ValueError("initID is not set")
        threads = []
        for serverIP in self._IPs:
            for node in self._nodes:
                if node._IP == serverIP:
                    INIT = 'docker exec -t %s geth --datadir abc init %s' % (node._name, self._cfgFile)
                    t = threading.Thread(target=serverIP.execCommand, args=(INIT,))
                    t.start()
                    threads.append(t)
        for t in threads:
            t.join()
        time.sleep(0.3)

    def runGethNodes(self):
#        print('run geth nodes:')
        threads = []
        count = 0
        for node in self._nodes:
            RUN = ('geth --datadir abc --cache 512 --port 30303 --rpcport 8545 --rpcapi admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr \"0.0.0.0\" '
                   '--pbftid %d --nodeindex %d --blockchainid %d --unlock %s --password '
                   '\"passfile\" --maxpeers 5000 --maxpendpeers 1000 --syncmode \"full\" --nodiscover') % (node._pbftid, node._nodeindex,
                                                                  node._blockchainid, node._accounts[0])
            CMD = 'docker exec -td %s %s' % (node._name, RUN)
            print(RUN)
            count += 1
            if count == 10:
                time.sleep(0.3)
                print("-----------------------geth in a chain---------------------")
                count = 0
            t = threading.Thread(target=node._IP.execCommand, args=(CMD,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        print('node starting...')
        for i in range(8):
            print('.', end='')
            time.sleep(1)

        threads = []
        for node in self._nodes:
            t = threading.Thread(target=node.setEnode)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        time.sleep(0.2)

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
        if not self._isTerminal:
            print("constructing single chain")
            startTime = time.time()
            threads = []
            count = 0
            for i in range(len(self._nodes)):
                for j in range(i+1, len(self._nodes)):
                    tmpEnode = self._nodes[j].getEnode()
                    count += 1
                    if count == 8:
                        time.sleep(0.2)
                        count = 0
                    t = threading.Thread(target=self._nodes[i].addPeer, args=(tmpEnode, 0))
                    t.start()
                    threads.append(t)
            for t in threads:
                t.join()
            endTime = time.time()
            print('%.3fs' % (endTime - startTime))
            print("-------------------------")
            time.sleep(0.2)

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
        time.sleep(0.3)
        threads = []
        count = 0
        for node in self._nodes:
            for other in otherChain._nodes:
                ep = node.Enode
                count += 1
                if count == 10:
                    count = 0
                    time.sleep(0.3)
                t = threading.Thread(target=other.addPeer, args=(ep, 2))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
        time.sleep(1)


    def connectUpperChain(self, otherChain):
        '''
        Connect to an upper single chain.
        '''
        time.sleep(0.3)
        threads = []
        count = 0
        for node in self._nodes:
            for other in otherChain._nodes:
                ep = other.Enode
                count += 1
                if count == 10:
                    count = 0
                    time.sleep(0.3)
                t = threading.Thread(target=node.addPeer, args=(ep, 2))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
        time.sleep(1)


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
        time.sleep(0.1*(len(self._nodes)//10+1))

    def setLevel(self, maxLevel):
        '''
        Set level info for each node.
        '''
        threadlist = []
        count = 0
        if not self._ifSetLevel:
            for node in self._nodes:
                count += 1
                if count == 10:
                    count = 0
                    time.sleep(0.2)
                t = threading.Thread(target = node.setLevel,args=(self._level,maxLevel))
                t.start()
                threadlist.append(t)
            for t in threadlist:
                t.join()
            self._ifSetLevel = True
        else:
            raise RuntimeError("level of chain %s already set" % self._id)

    def setID(self):
        '''
        Set ID for a blockchain.
        '''
        if not self._ifSetNumber and self._ifSetLevel:
            raise RuntimeError("number and level info should be set previously")
        if len(self._id) // 4 != self._level:
            raise ValueError("length of id should match level number")
        if not self._ifSetID:
            if self._level == 0:
                p = self.getPrimer()
                p.setID("")
            else:
                theadlist = []
                count = 0
                for node in self._nodes:
                    count += 1
                    if count == 5:
                        count = 0
                        time.sleep(0.5)
                    t = threading.Thread(target=node.setID,args=(self._id,))
                    t.start()
                    theadlist.append(t)
                for t in theadlist:
                    t.join()
            self._ifSetID = True
        else:
            raise RuntimeError("ID of chain %s already set" % self._id)


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    nodeNum = 4
    c = SingleChain('0001', 1, nodeNum, nodeNum*3//4+1, 121, IPlist)
    c.SinglechainStart()
    c.ConsensusChainConfig()
    c.runNodes()
#    p = c.getPrimer()
#    print(p.getPeerCount())
    for i in range(1, nodeNum+1):
        node = c.getNode(i)
#        acc = node.getAccounts()[0]
#        print(acc)
#        print(node.getBalance(acc))
        print(node.getPeerCount())
    c.destructChain()
