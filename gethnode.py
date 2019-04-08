
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from iplist import IPList, USERNAME, PASSWD
from time import sleep
from functools import wraps
from random import random

# class GethNode0(object):
#     '''data structure for geth client running in a docker container'''
#
#     def __init__(self, userName=USERNAME, passWord=PASSWD):
#         self.Enode = ''
#         self._IP, self._rpcPort, self._listenerPort = IPlist.getNewPort()
#         self._name = 'geth-pbft' + str(self._rpcPort)
#         self._headers = {'Content-Type': 'application/json', 'Connection': 'close'}
#         self._userName = USERNAME
#         self._passWord = PASSWD
#         self._accounts = []
#         self._ifSetGenesis = False
#
#     def start(self):
#         '''start a container for geth client '''
#         pass



class GethNode():
    '''Data structure for Geth-pbft client.'''

    def __init__(self, IPlist, pbftid, nodeindex, blockchainid, username=USERNAME, passwd=PASSWD):
        self.Enode = ''
        self._id = nodeindex
        self._IP, self._rpcPort, self._listenerPort = IPlist.getNewPort()
        self._pbftid = pbftid
        self._nodeindex = nodeindex
        self._blockchainid = blockchainid
        self._name = 'geth-pbft' + str(self._rpcPort)
        self._headers = {'Content-Type': 'application/json', 'Connection':'close'}
        self._username = USERNAME
        self._passwd = PASSWD
        self._accounts = []

    def start(self):
        '''Start a container for geth on remote server and create a new account.'''
        RUN_DOCKER = ('docker run -td -p %d:8545 -p %d:30303 --rm --name %s rkdghd/geth-pbft:id' % (self._rpcPort,
                                                                                                        self._listenerPort,
                                                                                                        self._name))
        sleep(0.4)
        try:
            result = self._IP.execCommand(RUN_DOCKER)
        except Exception as e:
            print('Docker start error. Container maybe already exists')
        if result:
            print(result)
            print('container of node %s of blockchain %s at %s:%s started' % (self._nodeindex, self._blockchainid,
                                                                                  self._IP._ipaddr, self._rpcPort))
        # else:
        #     raise RuntimeError('Docker start error. Container maybe already exists')
        sleep(0.5)
        NEWACCOUNT = 'docker exec -t %s geth --datadir abc account new --password passfile' % self._name
        account = self._IP.execCommand(NEWACCOUNT).split()[-1][1:-1]
        sleep(0.3)
        if len(account) == 40:
            self._accounts.append(account)

    def rpcCall(self, method, params):
        '''Make a rpc call'''
        data = json.dumps({  ## json string used in HTTP requests
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self._id
        })
        url = "http://{}:{}".format(self._IP._ipaddr, self._rpcPort)
        with requests.Session() as r:
            response = r.post(url=url, data=data, headers=self._headers)
            content = json.loads(response.content.decode(encoding='utf-8'))
            print(content)
            result = content.get('result')
        print('%s @%s : %s    %s' % (method, self._IP._ipaddr, self._rpcPort, result))
        return result



    # def rpc(fn):
    #     '''Decorator for rpc calls.'''
    #     @wraps(fn)
    #     def func(self, *args, **kwargs):
    #         method, params = fn(self, *args, **kwargs)
    #         data = json.dumps({             ## json string used in HTTP requests
    #             'jsonrpc': '2.0',
    #             'method': method,
    #             'params': params,
    #             'id':self._id
    #             })
    #         url = "http://{}:{}".format(self._IP._ipaddr, self._rpcPort)
    #         sleep(0.2) # important
    #         with requests.Session() as r:
    #             response = r.post(url=url, data=data, headers=self._headers)
    #             content = json.loads(response.content.decode(encoding='utf-8'))
    #             print(content)
    #             result = content['result']
    #
    #         print('%s @%s : %s    %s' % (method, self._IP._ipaddr, self._rpcPort, result))
    #
    #         def _setNewAccount(acc):  return self._accounts.append(acc[2:])
    #
    #         def _printTxpool(result):  print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16),
    #                                                                                      int(result['queued'], 16)))
    #         def _hex2Dec(num):  return int(num, 16) if num else 0
    #
    #         def _setEnode(result):
    #             enode = result['enode'].split('@')[0]
    #             self.Enode = '{}@{}:{}'.format(enode, self._IP._ipaddr, self._listenerPort)
    #             return enode
    #
    #         def _txHash(result):  return result['hash']
    #
    #         postRPC = { 'personal_newAccount': _setNewAccount,
    #                   'net_peerCount': _hex2Dec,
    #                   'eth_getBlockTransactionCountByNumber': _hex2Dec,
    #                   'admin_nodeInfo': _setEnode,
    #                   'txpool_status': _printTxpool,
    #                   'eth_getTransactionByBlockNumberAndIndex': _txHash
    #                 }
    #         if method in postRPC:
    #             result = postRPC[method](result)
    #         return result
    #     return func

    def getEnode(self):
        '''Return enode information from admin.nodeInfo'''
        return self.Enode

    def getPeerCount(self):
        '''net.peerCount'''
        method = 'net_peerCount'
        params = []
        result = self.rpcCall(method, params)
        return int(result, 16) if result else 0    # change hex number to dec

    def getPeers(self):
        '''admin.peers'''
        method = 'admin_peers'
        params = []
        return self.rpcCall(method, params)

    def newAccount(self, password='root'):
        '''personal.newAccount(password)'''
        method = 'personal_newAccount'
        params = [password]
        account = self.rpcCall(method, params)
        sleep(0.1)
        self._accounts.append(account[2:])

    def keyStatus(self):
        '''admin.keystatus()'''
        method = 'admin_keyStatus'
        params = []
        return self.rpcCall(method, params)

    def unlockAccount(self, account='0', password='root', duration=86400):
        '''personal.unlockAccount()'''
        method = 'personal_unlockAccount'
        params = [account, password, duration]
        return self.rpcCall(method, params)

    def sendOldTransaction(self, toID, toIndex, value, *args, **kwargs):
        '''eth.sendTransaction()'''
        if isinstance(value, int):    # if value is int, change it to hex str
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value}]
        method = 'eth_sendTransaction'
        sleep(0.2)
        return self.rpcCall(method, params)

    def sendTransaction(self, toID, toIndex, value, *args, **kwargs):
        '''eth.sendTransaction2()'''
        if isinstance(value, int):    # if value is int, change it to hex str
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value}]
        method = 'eth_sendTransaction2'
        sleep(0.2)
        return self.rpcCall(method, params)

    def testSendTransaction(self, toID, toIndex, value, interval, period, **kwargs):
        '''eth.testSendTransaction2()'''
        if isinstance(value, int):    # if value is int, change it to hex str
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value, "txinterval":interval, "txperiod":period}]
        method = 'eth_testSendTransaction2'
        sleep(0.2)
        return self.rpcCall(method, params)

    def getTransaction(self, TXID, *args, **kwargs):
        '''eth.getTransaction()'''
        method = 'eth_getTransaction'
        params = [TXID]
        return self.rpcCall(method, params)

    def getAccounts(self, *args, **kwargs):
        '''eth.accounts'''
        method = 'eth_accounts'
        params = []
        return self.rpcCall(method, params)

    def getBalance(self, account, *args, **kwargs):
        '''eth.getBalance()'''
        if not account.startswith('0x'):
            account = '0x' + account
        method = 'eth_getBalance'
        params = [account, 'latest']
        return self.rpcCall(method, params)

    def getBlockTransactionCount(self, index, *args, **kwargs):
        '''eth.getBlockTransactionCount()'''
        method = 'eth_getBlockTransactionCountByNumber'
        params = [hex(index)]
        result = self.rpcCall(method, params)
        return int(result, 16) if result else 0  # change hex number to dec


    def addPeer(self, *args, **kwargs):
        '''admin.addPeer()'''
        method = 'admin_addPeer'
        params = args
        sleep(0.1)
        return self.rpcCall(method, params)

#    def addPeer(self, *args, **kwargs):
#        '''IPC version'''
#        try:
#            CMD = ("docker exec -t %s geth attach ipc://root/abc/geth.ipc "
#                   "--exec \"admin.addPeer%s\"" %(self._name, args))
#            self._IP.execCommand(CMD)
#            sleep(1)
#        except Exception as e:
#            if self._exception is False:
#                self._exception = True
#                self._IP.execCommand(CMD)
#                sleep(1)
#            else:
#                raise RuntimeError('%s:%s %s %s' % (self._IP, self._listenerPort, self._rpcPort, e))

    def setEnode(self, *args, **kwargs):
        '''Set Enode info of a node.'''
        method = 'admin_nodeInfo'
        params = []
        result = self.rpcCall(method, params)    # result from rpc call
        enode = result['enode'].split('@')[0]
        self.Enode = '{}@{}:{}'.format(enode, self._IP._ipaddr, self._listenerPort)

    def setNumber(self, n, t, *args, **kwargs):
        '''admin.setNumber()'''
        # Check if the input params are legal
        if n < t:
            raise ValueError('nodeCount should be no less than threshold value')
        if t <= 0 or n <= 0:
            raise ValueError('nodeCount and threshold value should be positive')

        method = 'admin_setNumber'
        params = [n, t]
        sleep(0.1)
        return self.rpcCall(method, params)

    def setLevel(self, level, maxLevel, *args, **kwargs):
        '''admin.setLevel()'''
        # Check if the input params are legal
        if maxLevel < level:
            raise ValueError('level should be no larger than maxLevel')
        if level < 0:
            raise ValueError('level shoud be non-negative')

        method = 'admin_setLevel'
        params = [maxLevel, level]
        sleep(0.1)
        return self.rpcCall(method, params)

    def setID(self, ID, *args, **kwargs):
        '''admin.setID()'''
        method = 'admin_setID'
        params = [ID]
        sleep(0.1)
        return self.rpcCall(method, params)

    def txpoolStatus(self, *args, **kwargs):
        '''txpool.status'''
        method = 'txpool_status'
        params = []
        result = self.rpcCall(method, params)
        sleep(0.1)
        print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16),
                                                   int(result['queued'], 16)))

    def startMiner(self, *args, **kwargs):
        '''miner.start()'''
        method = 'miner_start'
        params = []
        return self.rpcCall(method, params)

    def stopMiner(self, *args, **kwargs):
        '''miner.stop()'''
        method = 'miner_stop'
        params = []
        return self.rpcCall(method, params)

    def getBlockByNumber(self, blockNumber):
        '''eth.getBlock()'''
        # check if index is greater than or equal 0
        if blockNumber < 0:
            raise ValueError('blockNumber should be non-negative')

        blockNumberStr = hex(blockNumber)
        method = 'eth_getBlockByNumber'
        params = [blockNumberStr, 'true']
        sleep(0.1)
        return self.rpcCall(method, params)

    def getTransactionByBlockNumberAndIndex(self, blockNumber, index):

        blockNumberStr = hex(blockNumber)
        indexStr = hex(index)
        method = 'eth_getTransactionByBlockNumberAndIndex'
        params = [blockNumberStr, indexStr]
        result = self.rpcCall(method, params)    # result from rpc call
        return result['hash']

    def getTxProofByHash(self, TxHash):
        '''eth.getTxProofByHash()'''
        method = 'eth_getTxProofByHash'
        params = [TxHash]
        result = self.rpcCall(method, params)
        print("---------", result)
        return result

    def getTxProofByProof(self, TxProof):
        '''eth.getTxProofByProf()'''
        method = 'eth_getTxProofByProof'
        params = [TxProof]
        result = self.rpcCall(method, params)
        print("~~~~", result)
        return result

    def isGethRunning(self):
        '''Check if the client is running.'''
        CMD = 'docker exec -t %s geth attach ipc://root/abc/geth.ipc --exec "admin.nodeInfo"' % self._name
        result = self._IP.execCommand(CMD)
        return False if result.split(':')[0] == 'Fatal' else True

    def stop(self):
        '''Remove the geth-pbft node container on remote server.'''
        STOP_CONTAINER = "docker stop %s" % self._name
        self._IP.execCommand(STOP_CONTAINER)
        print('node %s of blockchain %s at %s:%s stopped' % (self._nodeindex, self._blockchainid,
                                                             self._IP._ipaddr, self._rpcPort))


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    n = GethNode(IPlist, 0, 1, 121)
    n.start()
    print(n._accounts)
    n.stop()