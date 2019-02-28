#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko
import threading
import time


class IP():
    '''
    Create an IP object with a list of rpc ports and a list of listener ports.
    '''
    def __init__(self, ip, currentPort=0):
        if len(ip.split('.')) < 4:
            raise ValueError('format of ip is not correct')
        self._maxPayload = 8  # maximum number of clients running on one server
        self._currentPort = currentPort
        self._ip = ip
        self._rpcPorts = range(8515, 8515 + self._maxPayload * 10, 10)
        self._listenerPorts = range(30313, 30313 + self._maxPayload * 10, 10)

    def __repr__(self):
        return self._ip

    def getNewPort(self):
        '''
        Return a tuple of a remote server:(ip, rpcPort, listenerPort).
        '''
        if self._currentPort >= self._maxPayload:
            raise ValueError("over load")
        result = (self._ip, self._rpcPorts[self._currentPort], self._listenerPorts[self._currentPort])
        self._currentPort += 1
        return result

    def getMaxPayload(self):
        return self._maxPayload

    def isFullLoaded(self):
        '''
        Decide whether the server is full loaded.
        '''
        return self._currentPort >= self._maxPayload

    def releaseAll(self):
        self._currentPort = 0


class IPList():
    '''
    Manage IPs and ports.
    '''
    def __init__(self, ipFile, currentIP=0):
        '''
        Read IPs from a file.
        '''
        self._currentIP = currentIP
        self._ips = []
        with open(ipFile, 'r') as f:
            for line in f.readlines():
                if line.strip():
                    self._ips.append(IP(line.strip()))

    def getIPs(self):
        '''
        Return an IP list.
        '''
        return self._ips

    def getFullCount(self):
        if len(self._ips):
            return len(self._ips) * self._ips[0].getMaxPayload()
        else:
            return 0

    def getNewPort(self):
        '''
        Get a new rpcPort and a new listenerPort from an IP addr.
        '''
        if self._currentIP >= len(self._ips):
            raise ValueError("over load")
        result = self._ips[self._currentIP].getNewPort()
        if self._ips[self._currentIP].isFullLoaded():
            self._currentIP += 1
        return result

    def releaseAll(self):
        self._currentIP = 0

def execCommand(cmd, ip, port=22, username='root', password='Blockchain17'):
    '''
    exec a command on remote server using SSH
    '''
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port, username, password)
    stdin, stdout, stderr = client.exec_command(cmd)
    if not stderr.read():
        result = stdout.read().strip().decode(encoding='utf-8')
    else:
        result = stderr.read().strip().decode(encoding='utf-8')
    return result

def stopAll(IP, passwd='Blockchain17'):
    '''
    stop all running containers on a remote server
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=IP, port=22, username='root', password=passwd)
    try:
        NAMES = "docker ps --format '{{.Names}}'"
        stdin, stdout, stderr = ssh.exec_command(NAMES)
        result = stdout.read()
        if result:
            result = result.decode(encoding='utf-8', errors='strict').split()
            print(' '.join(result))
            STOP = 'docker stop %s' % ' '.join(result)
            stdin, stdout, stderr = ssh.exec_command(STOP)
            result = stdout.read()
            if result:
                print("all nodes at %s stopped" % IP)
            elif not stderr:
                print(stderr)
#            return True if result else False
        elif not stderr:
            print(stderr)
    except Exception as e:
        print('stopAll', e)
    ssh.close()


def startDockerService(IPList):
    '''
    start docker service on remote server
    '''
    startTime = time.time()
    CMD = 'systemctl start docker'
    threads = []
    for ip in IPList._ips:
        print("%s at %s" % (CMD, ip))
        t = threading.Thread(target=execCommand, args=(CMD, ip._ip))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    endTime = time.time()
    print('start docker service on all services. elapsed time:', endTime-startTime)

def isDockerRunning(ip):
    '''
    check if docker service is running
    '''
    CMD = 'systemctl status docker'
    result = execCommand(CMD, ip).split("\n")
    if len(result) >= 5:
        return True
    else:
        return False

def stopAllContainers(IPlist):
    threads = []
    for ip in IPlist._ips:
        print("stop all docker containers at %s" % ip._ip)
        t = threading.Thread(target=stopAll, args=(ip._ip,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    f = IPList('ip.txt')
    ips = f.getIPs()
    for i in range(10):
        print(f.getNewPort())
