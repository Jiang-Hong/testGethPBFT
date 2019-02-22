#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gethnode import GethNode, stopAll, rmAll, execCommand
from ips import IPList
import threading
from genesis import confGenesis
from time import sleep
from tqdm import tqdm
import subprocess
import requests
import json

class SingleChain():
    '''
    Data structure for a set of Geth-pbft clients for a single blockchain.
    '''

    def __init__(self, name, level, nodeCount, threshold, blockchainid, IPlist, passwd='Blockchain17'):
        '''
        init a set of geth-pbft nodes for one blockchain.
        '''
        if nodeCount > IPlist.getFullCount():
            raise ValueError("not enough IPs")

        self._level = level
        self._id = name
        self.nodeCount = nodeCount
        self.threshold = threshold
        self._blockchainid = blockchainid
        self._iplist = IPlist
        self._passwd = passwd
        self._nodes = []
        self._ips = set()
        self._ifSetNumber = False
        self._ifSetLevel = False
        self._ifSetID = False
        self._isTerminal = False
        self._accounts = []

    def SinglechainStart(self):
        '''
        run a singlechain
        '''
#        threadlist = []
        for index in range(self.nodeCount):
            pbftid = index
            nodeindex = index + 1
            tmp = GethNode(self._iplist, pbftid, nodeindex, self._blockchainid, self._passwd)
            self._ips.add(tmp._ip)
            # xq start a thread， target stand for a function that you want to run ,args stand for the parameters
#            t = threading.Thread(target=tmp.start)
#            threadlist.append(t)
#            t.start()
            tmp.start()
            self._nodes.append(tmp)


#        for t in threadlist:
#            # xq threads must run the join function ,because the resources of main thread is needed
#            t.join()

        for index in range(self.nodeCount):
            self._accounts.append(self._nodes[index]._accounts[0])
#        print(self._accounts)

    def SinglechainConfig(self):
        '''
        set genesis.json for a blockchain & init with genesis.json
        '''
        confGenesis(self._blockchainid, self._accounts)

        for serverIP in self._ips:
#            CP_JSON = 'docker/%s.json root@%s:%s.json' % (self._blockchainid, serverIP, self._blockchainid)
            NAME = '%s.json' % self._blockchainid
            subprocess.run(['./sendFile.sh', NAME, serverIP], stdout=subprocess.PIPE)
            sleep(0.5)
            for node in self._nodes:
                if node._ip == serverIP:
                    CMD = 'docker cp %s.json %s:/root/%s.json' % (self._blockchainid, node._name, self._blockchainid)
                    result = execCommand(CMD, serverIP)
#                    print(result)
                    sleep(0.5)
                    INIT = 'docker exec -t %s geth --datadir abc init %s.json' % (node._name, self._blockchainid)
                    result = execCommand(INIT, serverIP)
#                    print(result)
                    sleep(1)

    def TerminalConfig(self):
        '''
        set genesis.json for terminal equipment.
        '''
        initID = str(self._blockchainid)
        print("blockchainid", self._blockchainid)
        print("config initID", initID)
        for serverIP in self._ips:
            NAME = '%s.json' % initID
            subprocess.run(['./sendFile.sh', NAME, serverIP], stdout=subprocess.PIPE)
            sleep(0.5)
            for node in self._nodes:
                if node._ip == serverIP:
                    CMD = 'docker cp %s.json %s:/root/%s.json' % (initID, node._name, initID)
                    result = execCommand(CMD, serverIP)
#                    print(result)
                    sleep(0.5)
                    INIT = 'docker exec -t %s geth --datadir abc init %s.json' % (node._name, initID)
                    result = execCommand(INIT, serverIP)
#                    print(result)
                    sleep(1)


    def runGethNodes(self):
        print('run geth nodes:')
        for node in tqdm(self._nodes):
#            RUN = ('geth --datadir abc --cache 512 --port 30303 --rpcport 8545 --rpcapi admin,eth,miner,web3,net,personal --rpc --rpcaddr \"0.0.0.0\" '
#                   '--pbftid %d --nodeindex %d --blockchainid %d --unlock %s --password '
#                   '\"passfile\" --syncmode \"full\" --nodiscover | tee %s') % (node._pbftid, node._nodeindex,
#                                                                  node._blockchainid, node._accounts[0], node._name)
#            print(RUN)
#            CMD = 'docker exec -t %s sh -c %s' % (node._name, RUN)
#            print(CMD)
            RUN = ('geth --datadir abc --cache 512 --port 30303 --rpcport 8545 --rpcapi admin,eth,miner,web3,net,personal --rpc --rpcaddr \"0.0.0.0\" '
                   '--pbftid %d --nodeindex %d --blockchainid %d --unlock %s --password '
                   '\"passfile\" --syncmode \"full\" --nodiscover') % (node._pbftid, node._nodeindex,
                                                                  node._blockchainid, node._accounts[0])
            CMD = 'docker exec -td %s %s' % (node._name, RUN)
            print(RUN)
            result = execCommand(CMD, node._ip)
            if result:
                print('run node', result)

            sleep(2)
            msg = node._msg("admin_nodeInfo", [])
            url = "http://{}:{}".format(node._ip, node._rpcPort)
            try:
                response = requests.post(url, headers=node._headers, data=msg)
                enode = json.loads(response.content.decode(encoding='utf-8'))['result']['enode'].split('@')[0]
                node.Enode = '{}@{}:{}'.format(enode, node._ip, node._listenerPort)
#                print(node.Enode)
            except Exception as e:
                print("getEnode", e)

            sleep(2)


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
#        primer = self.getPrimer()
#        pEnode = primer.Enode

        # add peer for each node
#        threadlist = []
#        for node in self._nodes[1:]:
#            t = threading.Thread(target=primer.addPeer,args=(node.getEnode(),0))
#            t.start()
#            threadlist.append(t)
#        for t in threadlist:
#            t.join()
        sleep(1)
        for i in range(len(self._nodes)):
            for j in range(len(self._nodes)):
                tmpEnode = self._nodes[j].getEnode()
                self._nodes[i].addPeer(tmpEnode, 0)


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
        sleep(1)
        for node in self._nodes:
            for other in otherChain._nodes:
                ep = other.Enode
                node.addPeer(ep, 1)
        sleep(3)
#        p1 = self.getPrimer()
#        p2 = otherChain.getPrimer()
#        ep2 = p2.Enode
#        p1.addPeer(ep2, 1)

    def connectUpperChain(self, otherChain):
        '''
        Connect to an upper single chain.
        '''
        sleep(1)
        for node in self._nodes:
            for other in otherChain._nodes:
                ep = other.Enode
                node.addPeer(ep, 2)
#        p1 = self.getPrimer()
#        p2 = otherChain.getPrimer()
#        ep2 = p2.Enode
#        p1.addPeer(ep2, 2)


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
            print("setNumber")
            p = self.getPrimer()
            p.setNumber(self.nodeCount, self.threshold)
            self._ifSetNumber = True
        else:
            raise RuntimeError("number of chain %s already set" % self._id)

    def setLevel(self, maxLevel):
        '''
        Set level info for each node.
        '''
#        threadlist = []
#        if not self._ifSetLevel:
#            for node in self._nodes:
#                t = threading.Thread(target = node.setLevel,args=(self._level,maxLevel))
#                t.start()
#                threadlist.append(t)
#            for t in threadlist:
#                t.join()
#            self._ifSetLevel = True
#        else:
#            raise RuntimeError("level of chain %s already set" % self._id)
        print("setLevel")
        for node in self._nodes:
            node.setLevel(self._level, maxLevel)


    def setID(self):
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
                print("set primer ID")
                p.setID("")
            else:
#                theadlist = []
#                for node in self._nodes:
#                    t = threading.Thread(target=node.setID,args=(self._id,))
#                    t.start()
#                    theadlist.append(t)
#                for t in theadlist:
#                    t.join()
                for node in self._nodes:
                    print("set node ID")
                    node.setID(self._id)
            self._ifSetID = True
        else:
            raise RuntimeError("ID of chain %s already set" % self._id)


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    nodeNum = 4
    c = SingleChain('1', 1, nodeNum, nodeNum*3//4+1, 121, IPlist)
    c.SinglechainStart()
    c.SinglechainConfig()
    c.runGethNodes()
    c.constructChain()
#    p = c.getPrimer()
#    print(p.getPeerCount())
    for i in range(1, nodeNum+1):
        node = c.getNode(i)
#        acc = node.getAccounts()[0]
#        print(acc)
#        print(node.getBalance(acc))
        print(node.getPeerCount())

    c.destructChain()
