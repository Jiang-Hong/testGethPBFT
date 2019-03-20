
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from ips import IPList, USERNAME, PASSWD
from time import sleep


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

    def _msg(self, method, params):
        '''
        Return json string used in HTTP requests.
        '''
        return json.dumps({
               "jsonrpc": "2.0",
               "method": method,
               "params": params,
               "id": self._id
               })

    def _rpcCall(self, method, params):
        data = json.dumps({                          ## json string used in HTTP requests
                    'jsonrpc': '2.0',
                    'method': method,
                    'params': params,
                    'id':self._id
                    })
        url = "http://{}:{}".format(self._IP._ipaddr, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=data)
            response.close()
            return json.loads(response.content.decode(encoding='utf-8'))['result']
        except Exception as e:
            raise RuntimeError(method, e)

    def getEnode(self):
        '''
        Return enode information from admin.nodeInfo.
        '''
        return self.Enode

    def getPeerCount(self):
        '''
        net.peerCount
        '''
        method = 'net_peerCount'
        params = []
        return int(self._rpcCall(method, params), 16)

    def getPeers(self):
        '''
        admin.peers
        '''
        method = 'admin_peers'
        params = []
        return self._rpcCall(method, params)

    def newAccount(self, password='root'):
        '''
        personal.newAccount(password)
        '''
        method = 'personal_newAccount'
        params = [password]
        result = self._rpcCall(method, params)
        self._accounts.append(result)
        return result

    def keyStatus(self):
        '''
        admin.keystatus()
        '''
        method = 'admin_keyStatus'
        params = []
        return self._rpcCall(method, params)

    def unlockAccount(self, account, password='root', duration=86400):
        '''
        personal.unlockAccount()
        '''
        method = 'personal_unlockAccount'
        params = [account, password, duration]
        return self._rpcCall(method, params)

    def sendOldTransaction(self, toID, toIndex, value):
        '''
        eth.sendTransaction()
        '''
        if isinstance(value, int):
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value}]
        method = 'eth_sendTransaction'
        return self._rpcCall(method, params)

    def sendTransaction(self, toID, toIndex, value):
        '''
        eth.sendTransaction2()
        '''
        if isinstance(value, int):
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value}]
        method = 'eth_sendTransaction2'
        return self._rpcCall(method, params)

    def testSendTransaction(self, toID, toIndex, value, interval, period):
        '''
        eth.testSendTransaction2()
        '''
        if isinstance(value, int):
            value = hex(value)
        params = [{"toid":toID, "toindex":toIndex, "value":value, "txinterval":interval, "txperiod":period}]
        method = 'eth_testSendTransaction2'
        return self._rpcCall(method, params)

    def getTransaction(self, TXID):
        '''
        eth.getTransaction()
        '''
        method = 'eth_getTransaction'
        params = [TXID]
        return self._rpcCall(method, params)

    def getAccounts(self):
        '''
        eth.accounts
        '''
        method = 'eth_accounts'
        params = []
        return self._rpcCall(method, params)

    def getBalance(self, account):
        '''
        eth.getBalance()
        ipc form: docker exec -it geth-pbft8515 geth attach ipc:abc/geth.ipc --exec "eth.getBalance(eth.accounts[0])"
        '''
        if not account.startswith('0x'):
            account = '0x' + account
        method = 'eth_getBalance'
        params = [account, 'latest']
        return self._rpcCall(method, params)

    def getBlockTransactionCount(self, index):
        '''
        eth.getBlockTransactionCount()
        '''
        method = 'eth_getBlockTransactionCountByNumber'
        params = [hex(index)]
        number = self._rpcCall(method, params)
        return int(number, 16) if number else None

    def addPeer(self, *param):
        '''
        admin.addPeer()
        '''
        method = 'admin_addPeer'
        params = param
        self._rpcCall(method, params)
#        sleep(0.5)

    def setNumber(self, n, t):
        '''
        admin.setNumber()
        '''
        if n < t:
            raise ValueError("nodeCount should be no less than threshold value")
        method = 'admin_setNumber'
        params = [n, t]
        result = self._rpcCall(method, params)
        print("node at %s:%d setNumber result: %s" % (self._IP._ipaddr, self._rpcPort, result))
        sleep(0.1)

    def setLevel(self, level, maxLevel):
        '''
        admin.setLevel()
        '''
        if maxLevel < level:
            raise ValueError("level should be no larger than maxLevel")
#        sleep(0.1)
        method = 'admin_setLevel'
        params = [maxLevel, level]
        result = self._rpcCall(method, params)
        print("node at %s:%d setLevel result: %s" % (self._IP._ipaddr, self._rpcPort, result))
#        sleep(0.1)

    def setID(self, ID):
        '''
        admin.setID()
        '''
#        sleep(0.3)
        method = 'admin_setID'
        params = [ID]
        result = self._rpcCall(method, params)
        print("node at %s:%d setID result: %s" % (self._IP._ipaddr, self._rpcPort, result))
#        sleep(0.2)

    def txpoolStatus(self):
        '''
        txpool.status
        '''
        method = 'txpool_status'
        params = []
        result = self._rpcCall(method, params)
        print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16), int(result['queued'], 16)))


    def startMiner(self):
        '''
        miner.start()
        '''
        method = 'miner_start'
        params = []
        self._rpcCall(method, params)
        print("miner at %s:%d start" % (self._IP._ipaddr, self._rpcPort))

    def stopMiner(self):
        '''
        miner.stop()
        '''
        method = 'miner_stop'
        params = []
        result = self._rpcCall(method, params)
        print("miner at %s:%d stop: %s" % (self._IP._ipaddr, self._rpcPort, result))

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