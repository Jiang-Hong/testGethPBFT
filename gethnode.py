# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from iplist import IPList
from const import USERNAME, PASSWD, SEMAPHORE
from time import sleep


# class GethNode0(object):
#     """data structure for geth client running in a docker container"""
#
#     def __init__(self, userName=USERNAME, passWord=PASSWD):
#         self.enode = ''
#         self.ip, self.rpc_port, self.ethereum_network_port = IPlist.getNewPort()
#         self.name = 'geth-pbft' + str(self.rpc_port)
#         self._headers = {'Content-Type': 'application/json', 'Connection': 'close'}
#         self._userName = USERNAME
#         self.password = PASSWD
#         self.accounts = []
#         self._ifSetGenesis = False
#
#     def start(self):
#         """start a container for geth client """
#         pass


class GethNode():
    """Data structure for Geth-pbft client."""

    def __init__(self, ip_list, pbft_id, node_index, blockchain_id, username=USERNAME, password=PASSWD):
        self.enode = ''
        self.id = node_index    # used in rpc call
        self.ip, self.rpc_port, self.ethereum_network_port = ip_list.get_new_port()
        self.pbft_id = pbft_id
        self.node_index = node_index
        self.blockchain_id = blockchain_id
        self.name = 'geth-pbft' + str(self.rpc_port)    # docker container name of this node
        self._headers = {'Content-Type': 'application/json', 'Connection': 'close'}    # for rpc call use
        self.username = username    # user name of login user of a server
        self.password = password    # password of login user of a server
        self.accounts = []    # accounts list of a geth node

    def start(self):
        """Start a container for geth on remote server and create a new account."""
        # --ulimit nofile=<soft limit>:<hard limit> set the limit for open files
        docker_run_command = ('docker run --ulimit nofile=65535:65535 -td -p %d:8545 -p %d:30303 --rm --name %s '
                              'rkdghd/geth-pbft:id' % (self.rpc_port, self.ethereum_network_port, self.name))
        sleep(0.4)
        result = self.ip.exec_command(docker_run_command)
        if result:
            if result.startswith('docker: Error'):
                print(result)
                raise RuntimeError('An error occurs while starting docker container. Container maybe already exists')
            print('container of node %s of blockchain %s at %s:%s started' % (self.node_index, self.blockchain_id,
                                                                              self.ip.address, self.rpc_port))
        new_account_command = 'docker exec -t %s geth --datadir abc account new --password passfile' % self.name
        sleep(0.1)
        account = self.ip.exec_command(new_account_command).split()[-1][1:-1]
        sleep(0.2)
        if len(account) == 40:    # check if the account is valid
            self.accounts.append(account)

    def rpc_call(self, method, params=[]):
        """Make a rpc call to this geth node."""
        data = json.dumps({  ## json string used in HTTP requests
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': self.id
        })
        url = "http://{}:{}".format(self.ip.address, self.rpc_port)
        SEMAPHORE.acquire()
        with requests.Session() as r:
            response = r.post(url=url, data=data, headers=self._headers)
            content = json.loads(response.content.decode(encoding='utf-8'))
            print(content)
            result = content.get('result')
        SEMAPHORE.release()
        err = content.get('error')
        if err:
            raise RuntimeError(err.get('message'))

        print('%s @%s : %s    %s' % (method, self.ip.address, self.rpc_port, result))
        return result

    def get_enode(self):
        """Return enode information from admin.nodeInfo"""
        return self.enode

    def get_peer_count(self):
        """net.peerCount"""
        method = 'net_peerCount'
        sleep(0.02)
        result = self.rpc_call(method)
        return int(result, 16) if result else 0  # change hex number to dec

    def get_peers(self):
        """admin.peers"""
        method = 'admin_peers'
        return self.rpc_call(method)

    def new_account(self, password='root'):
        """personal.newAccount(password)"""
        method = 'personal_newAccount'
        params = [password]
        account = self.rpc_call(method, params)
        sleep(0.1)
        self.accounts.append(account[2:])

    def key_status(self):
        """admin.key_status()"""
        method = 'admin_keyStatus'
        return self.rpc_call(method)

    def unlock_account(self, account='0', password='root', duration=86400):
        """personal.unlockAccount()"""
        method = 'personal_unlockAccount'
        params = [account, password, duration]
        return self.rpc_call(method, params)

    def send_old_transaction(self, to_id, to_index, value):
        """eth.sendTransaction()"""
        if isinstance(value, int):  # if value is int, change it to hex str
            value = hex(value)
        params = [{"toid": to_id, "toindex": to_ndex, "value": value}]
        method = 'eth_sendTransaction'
        sleep(0.2)
        return self.rpc_call(method, params)

    def send_transaction(self, to_id, to_index, value):
        """eth.sendTransaction2()"""
        if isinstance(value, int):  # if value is int, change it to hex str
            value = hex(value)
        params = [{"toid": to_id, "toindex": to_index, "value": value}]
        method = 'eth_sendTransaction2'
        sleep(0.2)
        return self.rpc_call(method, params)

    def test_send_transaction(self, to_id, to_index, value, interval, period):
        """eth.testSendTransaction2()"""
        if isinstance(value, int):  # if value is int, change it to hex str
            value = hex(value)
        params = [{"toid": to_id, "toindex": to_index, "value": value, "txinterval": interval, "txperiod": period}]
        method = 'eth_testSendTransaction2'
        sleep(0.2)
        return self.rpc_call(method, params)

    def get_transaction(self, transaction_id):
        """eth.getTransaction()"""
        method = 'eth_getTransaction'
        params = [transaction_id]
        return self.rpc_call(method, params)

    def get_accounts(self):
        """eth.accounts"""
        method = 'eth_accounts'
        return self.rpc_call(method)

    def get_balance(self, account):
        """eth.getBalance()"""
        if not account.startswith('0x'):
            account = '0x' + account
        method = 'eth_getBalance'
        params = [account, 'latest']
        return self.rpc_call(method, params)

    def get_block_transaction_count(self, index):
        """eth.getBlockTransactionCount()"""
        method = 'eth_getBlockTransactionCountByNumber'
        params = [hex(index)]
        result = self.rpc_call(method, params)
        return int(result, 16) if result else 0  # change hex number to dec

    def add_peer(self, *args):
        """admin.addPeer()"""
        method = 'admin_addPeer'
        params = list(args)
        result = self.rpc_call(method, params)
        return result

    #    def addPeer(self, *args, **kwargs):
    #        """IPC version"""
    #        try:
    #            CMD = ("docker exec -t %s geth attach ipc://root/abc/geth.ipc "
    #                   "--exec \"admin.addPeer%s\"" %(self.name, args))
    #            self.ip.exec_command(CMD)
    #            sleep(1)
    #        except Exception as e:
    #            if self._exception is False:
    #                self._exception = True
    #                self.ip.exec_command(CMD)
    #                sleep(1)
    #            else:
    #                raise RuntimeError('%s:%s %s %s' % (self.ip, self.ethereum_network_port, self.rpc_port, e))

    def set_enode(self):
        """Set enode info of a node."""
        method = 'admin_nodeInfo'
        result = self.rpc_call(method)  # result from rpc call
        enode = result['enode'].split('@')[0]
        self.enode = '{}@{}:{}'.format(enode, self.ip.address, self.ethereum_network_port)

    def set_number(self, node_count, thresh):
        """admin.set_number()"""
        # Check if the input params are legal
        if node_count < thresh:
            raise ValueError('nodeCount should be no less than threshold value')
        if thresh <= 0 or node_count <= 0:
            raise ValueError('nodeCount and threshold value should be positive')

        method = 'admin_setNumber'
        params = [node_count, thresh]
        sleep(0.1)
        return self.rpc_call(method, params)

    def set_level(self, level, max_level):
        """admin.setLevel()"""
        # Check if the input params are legal
        if max_level < level:
            raise ValueError('level should be no larger than maxLevel')
        if level < 0:
            raise ValueError('level shoud be non-negative')

        method = 'admin_setLevel'
        params = [max_level, level]
        sleep(0.1)
        return self.rpc_call(method, params)

    def set_id(self, chain_id):
        """admin.setID()"""
        method = 'admin_setID'
        params = [chain_id]
        # sleep(0.1)
        return self.rpc_call(method, params)

    def txpool_status(self):
        """txpool.status"""
        method = 'txpool_status'
        result = self.rpc_call(method)
        sleep(0.1)
        print("txpool.status pending:%d, queued:%d" % (int(result['pending'], 16),
                                                       int(result['queued'], 16)))

    def start_miner(self):
        """miner.start()"""
        method = 'miner_start'
        return self.rpc_call(method)

    def stop_miner(self):
        """miner.stop()"""
        method = 'miner_stop'
        return self.rpc_call(method)

    def get_block_by_number(self, block_number):
        """eth.getBlock()"""
        # check if index is greater than or equal 0
        if block_number < 0:
            raise ValueError('blockNumber should be non-negative')

        block_number_hex_string = hex(block_number)
        method = 'eth_getBlockByNumber'
        params = [block_number_hex_string, 'true']
        sleep(0.1)
        return self.rpc_call(method, params)

    def get_transaction_by_block_number_and_index(self, block_number, index):

        block_number_hex_string = hex(block_number)
        index_hex_string = hex(index)
        method = 'eth_getTransactionByBlockNumberAndIndex'
        params = [block_number_hex_string, index_hex_string]
        result = self.rpc_call(method, params)  # result from rpc call
        return result['hash']

    def get_transaction_proof_by_hash(self, transaction_hash):
        """eth.getTxProofByHash()"""
        method = 'eth_getTxProofByHash'
        params = [transaction_hash]
        result = self.rpc_call(method, params)
        print(result)
        return result

    def get_transaction_proof_by_proof(self, transaction_proof):
        """eth.getTxProofByProf()"""
        method = 'eth_getTxProofByProof'
        params = [transaction_proof]
        result = self.rpc_call(method, params)
        print(result)
        return result

    def is_geth_running(self):
        """Check if the client is running."""
        command = 'docker exec -t %s geth attach ipc://root/abc/geth.ipc --exec "admin.nodeInfo"' % self.name
        result = self.ip.exec_command(command)
        return False if result.split(':')[0] == 'Fatal' else True

    def stop(self):
        """Remove the geth-pbft node container on remote server."""
        stop_command = "docker stop %s" % self.name
        self.ip.exec_command(stop_command)
        print('node %s of blockchain %s at %s:%s stopped' % (self.node_index, self.blockchain_id,
                                                             self.ip.address, self.rpc_port))


if __name__ == "__main__":
    IPlist = IPList('ip.txt')
    n = GethNode(IPlist, 0, 1, 121)
    n.start()
    print(n.accounts)
    n.stop()
