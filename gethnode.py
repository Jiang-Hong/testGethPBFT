#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import paramiko
import requests
import json
from time import sleep

class GethNode():
    '''
    Data structure for Geth-pbft client.
    '''

    def __init__(self, ip, pbftid, nodeindex, blockchainid, rpcPort=8515, listenerPort=30313, passwd='Blockchain17'):
        '''
        Start a geth-pbft node on remote server.
        '''

        self._id = nodeindex
        self._ip = ip
        self._rpcPort = rpcPort
        self._listenerPort = listenerPort
        self._pbftid = pbftid
        self._nodeindex = nodeindex
        self._blockchainid = blockchainid
        self._name = 'geth-pbft' + str(rpcPort)
        self._headers = {'Content-Type': 'application/json'}
        self._passwd = passwd

        # docker command to run on remote server.
        RUN_DOCKER = ('docker run -p %d:8545 -p %d:30303 --rm --name %s rkdghd/geth-pbft --rpcapi admin,eth,miner,web3,net '
                       '--rpc --rpcaddr \"0.0.0.0\" --datadir /root/abc --pbftid %d --nodeindex %d '
                       '--blockchainid %d &') % (rpcPort, listenerPort, self._name, pbftid, nodeindex, blockchainid)

        # print(RUN_DOCKER)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=22, username='root', password=self._passwd)
        try:
            stdin, stdout, stderr = ssh.exec_command(RUN_DOCKER)
            result = stdout.read()
            if result:
                print('node at %s:%s started' % (self._ip, self._listenerPort))
            else:
                print(stderr)
            # result = stdout.read()
            # print(result)
            ssh.close()
        except Exception as e:
            print(e)

    def __msg(self, method, params):
        '''
        Return json string used in HTTP requests.
        '''

        return json.dumps({
               "jsonrpc": "2.0",
               "method": method,
               "params": params,
               "id": self._id
               })

    def getEnode(self):
        '''
        Return enode information from admin.nodeInfo.
        '''

        sleep(2.5)
        msg = self.__msg("admin_nodeInfo", [])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            enode = json.loads(response.content.decode(encoding='utf-8'))['result']['enode'].split('@')[0]
            return '{}@{}:{}'.format(enode, self._ip, self._listenerPort)
        except Exception as e:
            print("getEnode", e)

    def getPeerCount(self):
        '''
        net.peerCount
        '''

        sleep(2)
        msg = self.__msg("net_peerCount", [])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            count = int(json.loads(response.content.decode(encoding='utf-8'))['result'], 16)
            return count
        except Exception as e:
            print("getPeerCount", e)

    def getPeers(self):
        '''
        admin.peers
        '''
        sleep(2)
        msg = self.__msg("admin_peers", [])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            peers = json.loads(response.content.decode(encoding='utf-8'))
            return peers
        except Exception as e:
            print("getPeers", e)

    def addPeer(self, *param):
        '''
        admin.addPeer()
        '''

        sleep(3)
        msg = self.__msg("admin_addPeer", param)
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            requests.post(url, headers=self._headers, data=msg)
            # print(response.content)
        except Exception as e:
            print("addPeer", e)

    def setNumber(self, n, t):
        '''
        admin.setNumber()
        '''
        assert n >= t, "n should be no less than t"
        sleep(2)
        msg = self.__msg("admin_setNumber", [n, t])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            print(response.content)
        except Exception as e:
            print("setNumber", e)

    def setLevel(self, level, maxLevel):
        '''
        admin.setLevel()raise
        '''
        assert maxLevel >= level, "level should be no larger than maxLevel"
        sleep(2)
        msg = self.__msg("admin_setLevel", [maxLevel, level])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            print(response.content)
        except Exception as e:
            print("setLevel", e)

    def setID(self, id):
        '''
        admin.setID()
        '''
        sleep(2)
        msg = self.__msg("admin_setID", ['%d'.format(id)])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            print(response.content)
        except Exception as e:
            print("setID", e)

    def testHIBE(self, txString):
        '''
        admin.testhibe()
        '''
        sleep(2)
        msg = self.__msg("admin_testhibe", ['%d'.format(txString)])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            print(response.content)
        except Exception as e:
            print("testHIBE", e)

    def isRunning(self):
        '''
        Check if the client is running.
        '''
        sleep(1)
        msg = self.__msg("admin_nodeInfo", [])
        url = "http://{}:{}".format(self._ip, self._rpcPort)
        try:
            response = requests.post(url, headers=self._headers, data=msg)
            return True if response else False
        except Exception as e:
            print("isRunning", e)

    def stop(self):
        '''
        Remove the geth-pbft node container on remote server.
        '''
        sleep(1)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self._ip, port=22, username='root', password=self._passwd)
        STOP_CONTAINER = "docker stop %s" % self._name
        try:
            stdin, stdout, stderr = ssh.exec_command(STOP_CONTAINER)
            result = stdout.read()
            ssh.close()
            if result:
                print('node at %s:%s stopped' % (self._ip, self._listenerPort))
            elif not stderr:
                print(stderr)
            return True if result else False
        except Exception as e:
            print("stop", e)