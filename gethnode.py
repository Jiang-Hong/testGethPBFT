
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from ips import IPList, USERNAME, PASSWD
from time import sleep
from functools import wraps


class GethNode():
    '''
    Data structure for Geth-pbft client.
    '''

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
        self._tmp = []

    def start(self):
        '''
        Start a geth-pbft node on remote server.
        '''
        RUN_DOCKER = ('docker run -td -p %d:8545 -p %d:30303 --rm --name %s rkdghd/geth-pbft:id' % (self._rpcPort,
                                                                                                        self._listenerPort,
                                                                                                        self._name))

        result = self._IP.execCommand(RUN_DOCKER)
        if result:
            print('container of node %s of blockchain %s at %s:%s started' % (self._nodeindex, self._blockchainid,
                                                                                  self._IP._ipaddr, self._rpcPort))
        else:
            raise RuntimeError('Docker start error. Container maybe already exists')
        sleep(0.6)
        NEWACCOUNT = 'docker exec -t %s geth --datadir abc account new --password passfile' % self._name
        account = self._IP.execCommand(NEWACCOUNT).split()[-1][1:-1]
#        print(account)
        if len(account) == 40:
            self._accounts.append(account)

    def rpc(fn):
        @wraps(fn)
        def func(self, *args, **kwargs):
            method, params = fn(self, *args, **kwargs)
            data = json.dumps({             ## json string used in HTTP requests
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
                'id':self._id
                })
            url = "http://{}:{}".format(self._IP._ipaddr, self._rpcPort)
            try:
                response = requests.post(url, headers=self._headers, data=data)
                response.close()
                result = json.loads(response.content.decode(encoding='utf-8'))['result']
            except Exception as e:
                raise RuntimeError(method, e)
            print('%s@%s:%s %s' % (method, self._IP._ipaddr, self._rpcPort, result))

            _setNewAccount = lambda acc: self._accounts.append(acc[2:])
            _printTxpool = lambda result: print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16), int(result['queued'], 16)))
            def _hex2Dec(num):
                return int(num, 16) if num else 0
            def _setEnode(result):
                enode = result['enode'].split('@')[0]
                self.Enode = '{}@{}:{}'.format(enode, self._IP._ipaddr, self._listenerPort)
                return enode
            table = { 'personal_newAccount': _setNewAccount,
                      'net_peerCount': _hex2Dec,
                      'eth_getBlockTransactionCountByNumber': _hex2Dec,
                      'admin_nodeInfo': _setEnode,
                      'txpool_status': _printTxpool
                    }
            if method in table:
                result = table[method](result)
            return result
        return func

    def getEnode(self):
        '''
        Return enode information from admin.nodeInfo.
        '''
        return self.Enode

    @rpc
    def getPeerCount(self, *args, **kwargs):
        method = 'net_peerCount'
        params = []
        return method, params

    @rpc
    def getPeers(self, *args, **kwargs):
        '''
        admin.peers
        '''
        method = 'admin_peers'
        params = []
        return method, params

    @rpc
    def newAccount(self, password='root', *args, **kwargs):  # 'root' is the default password of the new account
        '''
        personal.newAccount(password)
        '''
        method = 'personal_newAccount'
        params = [password]
        return method, params

    @rpc
    def keyStatus(self, *args, **kwargs):
        '''
        admin.keystatus()
        '''
        method = 'admin_keyStatus'
        params = []
        return method, params

    @rpc
    def unlockAccount(self, account, *args, password='root', duration=86400, **kwargs):
        '''
        personal.unlockAccount()
        '''
        method = 'personal_unlockAccount'
        params = [account, password, duration]
        return method, params

    @rpc
    def sendOldTransaction(self, toID, toIndex, value, *args, **kwargs):
        '''
        eth.sendTransaction()
        '''
        if isinstance(value, int):
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value}]
        method = 'eth_sendTransaction'
        return method, params

    @rpc
    def sendTransaction(self, toID, toIndex, value, *args, **kwargs):
        '''
        eth.sendTransaction2()
        '''
        if isinstance(value, int):
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value}]
        method = 'eth_sendTransaction2'
        return method, params

    @rpc
    def testSendTransaction(self, toID, toIndex, value, interval, period, *args, **kwargs):
        '''
        eth.testSendTransaction2()
        '''
        if isinstance(value, int):
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value, "txinterval":interval, "txperiod":period}]
        method = 'eth_testSendTransaction2'
        return method, params

    @rpc
    def getTransaction(self, TXID, *args, **kwargs):
        '''
        eth.getTransaction()
        '''
        method = 'eth_getTransaction'
        params = [TXID]
        return method, params

    @rpc
    def getAccounts(self, *args, **kwargs):
        '''
        eth.accounts
        '''
        method = 'eth_accounts'
        params = []
        return method, params

    @rpc
    def getBalance(self, account, *args, **kwargs):
        '''
        eth.getBalance()
        ipc form: docker exec -it geth-pbft8515 geth attach ipc:abc/geth.ipc --exec "eth.getBalance(eth.accounts[0])"
        '''
        if not account.startswith('0x'):
            account = '0x' + account
        method = 'eth_getBalance'
        params = [account, 'latest']
        return method, params

    @rpc
    def getBlockTransactionCount(self, index, *args, **kwargs):
        '''
        eth.getBlockTransactionCount()
        '''
        method = 'eth_getBlockTransactionCountByNumber'
        params = [hex(index)]
        return method, params

    @rpc
    def addPeer(self, *args, **kwargs):
        '''
        admin.addPeer()
        '''
        method = 'admin_addPeer'
        params = args
        return method, params

    @rpc
    def setEnode(self, *args, **kwargs):
        method = 'admin_nodeInfo'
        params = []
        return method, params

    @rpc
    def setNumber(self, n, t, *args, **kwargs):
        '''
        admin.setNumber()
        '''
        if n < t:
            raise ValueError("nodeCount should be no less than threshold value")
        method = 'admin_setNumber'
        params = [n, t]
        return method, params

    @rpc
    def setLevel(self, level, maxLevel, *args, **kwargs):
        '''
        admin.setLevel()
        '''
        if maxLevel < level:
            raise ValueError("level should be no larger than maxLevel")
#        sleep(0.1)
        method = 'admin_setLevel'
        params = [maxLevel, level]
        return method, params

    @rpc
    def setID(self, ID, *args, **kwargs):
        '''
        admin.setID()
        '''
#        sleep(0.3)
        method = 'admin_setID'
        params = [ID]
        return method, params

    @rpc
    def txpoolStatus(self, *args, **kwargs):
        '''
        txpool.status
        '''
        method = 'txpool_status'
        params = []
        return method, params
#        print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16), int(result['queued'], 16)))

    @rpc
    def startMiner(self, *args, **kwargs):
        '''
        miner.start()
        '''
        method = 'miner_start'
        params = []
        return method, params

    @rpc
    def stopMiner(self, *args, **kwargs):
        '''
        miner.stop()
        '''
        method = 'miner_stop'
        params = []
        return method, params

    def isGethRunning(self):
        '''
        Check if the client is running.
        '''
        CMD = 'docker exec -t %s geth attach ipc:/root/abc/geth.ipc --exec "admin.nodeInfo"' % self._name
        result = self._IP.execCommand(CMD)
        if result.split(':')[0] == 'Fatal':
            return False
        else:
            return True

    def stop(self):
        '''
        Remove the geth-pbft node container on remote server.
        '''
        STOP_CONTAINER = "docker stop %s" % self._name
        self._IP.execCommand(STOP_CONTAINER)
        print('node %s of blockchain %s at %s:%s stopped' % (self._nodeindex, self._blockchainid, self._IP._ipaddr, self._rpcPort))


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    n = GethNode(IPlist, 0, 1, 121)
    n.start()
    print(n._accounts)
    n.stop()