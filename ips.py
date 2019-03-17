#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko
import threading
import time
import subprocess

USERNAME = 'dell' #"dell"
PASSWD = 'dell@2017' #"dell@2017"

class IP():
    '''
    Create an IP object with a list of rpc ports and a list of listener ports.
    '''
    def __init__(self, ip, currentPort=0, username=USERNAME, password=PASSWD):
        if len(ip.split('.')) < 4:
            print("ip is", ip)
            raise ValueError('format of ip is not correct')
        self._maxPayload = 20  # maximum number of clients running on one server
        self._currentPort = currentPort
        self._ip = ip
        self._rpcPorts = range(8515, 8515 + self._maxPayload * 10, 10)
        self._listenerPorts = range(30313, 30313 + self._maxPayload * 10, 10)
        self._username = username
        self._password = password

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

    def releasePorts(self):
        self._currentPort = 0

    def stopContainers(self):
        pass


class IPList():
    '''
    Manage IPs and ports.
    '''
    def __init__(self, ipFile, currentIP=0, username=USERNAME, password=PASSWD):
        '''
        Read IPs from a file.
        '''
        self._currentIP = currentIP
        self._ips = []
        with open(ipFile, 'r') as f:
            for line in f.readlines():
                if line.strip():
                    self._ips.append(IP(line.strip()))
                else:
                    break

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

    def stopAll(self):
        pass

def execCommand(cmd, ip, port=22, username=USERNAME, password=PASSWD):
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
    client.close()
    return result

def stopAll(IP, username=USERNAME, password=PASSWD):
    '''
    stop all running containers on a remote server
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=IP, port=22, username=username, password=password)
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
    CMD = 'echo %s | sudo systemctl start docker' % (PASSWD)

    for ip in IPList._ips:
        myCMD = ['ssh-keyscan'] + [ip._ip]
        with open('/home/rkd/.ssh/known_hosts', 'a') as outfile:
            subprocess.run(myCMD, stdout=outfile)

    threads = []
    for ip in IPList._ips:
        print("%s at %s" % (CMD, ip))
        t = threading.Thread(target=execCommand, args=(CMD, ip._ip))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    endTime = time.time()
    print('docker service started on all servers')
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

def rebootServer(IPlist):
    threads = []
    for ip in IPlist._ips:
        print("reboot server %s" % ip._ip)
        t = threading.Thread(target=execCommand, args=('reboot', ip._ip))
        t.start()
        threads.append(t)
#        execCommand('reboot', ip._ip)
    for t in threads:
        t.join()

def shutdownServer(IPlist, username=USERNAME, password=PASSWD):
    '''
    shutdown all server on IPlist
    note: should set param shell=True
    '''
    for ip in IPlist._ips:
        my_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (password, password, username, ip)
        print("server %s poweroff" % ip._ip)
        subprocess.run(my_cmd, stdout=subprocess.PIPE, shell=True)

if __name__ == "__main__":
    f = IPList('ip.txt')
    ips = f.getIPs()
    for i in range(10):
        print(f.getNewPort())
    startDockerService(f)
