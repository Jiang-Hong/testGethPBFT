#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko
import threading
import time
import subprocess
import os

USERNAME = 'dell' # username of servers
PASSWD = 'dell@2017' # password of servers
MAXPAYLOAD = 15 # maximum number of clients running on one server

class IP():
    '''
    Create an IP object from a server with a list of rpc ports and a list of listener ports.
    '''
    def __init__(self, ipaddr, currentPort=0, username=USERNAME, password=PASSWD):
        if len(ipaddr.split('.')) < 4:
            print("ip is", ipaddr)
            raise ValueError('format of ip is not correct')
        self._maxPayload = MAXPAYLOAD
        self._currentPort = currentPort
        self._ipaddr = ipaddr
        self._rpcPorts = range(8515, 8515 + self._maxPayload * 10, 10)
        self._listenerPorts = range(30313, 30313 + self._maxPayload * 10, 10)
        self._username = username
        self._password = password

    def __repr__(self):
        return self._ipaddr

    def getNewPort(self):
        '''Return a tuple from a remote server:(IPaddr, rpcPort, listenerPort).'''
        if self._currentPort >= self._maxPayload:
            raise ValueError("over load")
        result = (self._rpcPorts[self._currentPort], self._listenerPorts[self._currentPort])
        self._currentPort += 1
        return result

    def getMaxPayload(self):
        '''Return the maximum containers able to run on the server.'''
        return self._maxPayload

    def isFullLoaded(self):
        '''Decide whether the server is full loaded.'''
        return self._currentPort >= self._maxPayload

    def releasePorts(self):
        self._currentPort = 0

    def execCommand(self, cmd, port=22):
        '''
        Exec a command on remote server using SSH connection.
        Note: If the concurrency of SSH commands is high, waiting time should be set.
        '''
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self._ipaddr, port, self._username, self._password)
        time.sleep(0.1)
        stdin, stdout, stderr = client.exec_command(cmd)
        time.sleep(0.1)
        if not stderr.read():
            result = stdout.read().strip().decode(encoding='utf-8')
            client.close()
            return result
        else:
            result = stderr.read().strip().decode(encoding='utf-8')
            print(result)
            client.close()
            if result:
                raise RuntimeError("exec command error: %s" % cmd)

    def isDockerRunning(self):
        '''Check if docker service is running on specified ip.'''
        CMD = 'systemctl status docker'
        result = self.execCommand(CMD).split("\n")
        return True if len(result) >= 5 else False

    def stopContainers(self):
        '''Stop all containers on the server.'''
        NAMES = "docker ps --format '{{.Names}}'"
        result = self.execCommand(NAMES).split()
        print('-----------')
        print(' '.join(result))
        STOP = 'docker stop %s' % ' '.join(result)
        result = self.execCommand(STOP)
        print("all nodes at %s stopped" % self._ipaddr)
        print('-----------')

    def rebootServer(self):
        '''Reboot remote server with SSH connection.'''
        my_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo reboot' % (self._password, self._password, self._username, self._ipaddr)
        print("server %s reboot" % self._ipaddr)
        subprocess.run(my_cmd, stdout=subprocess.PIPE, shell=True)

    def shutdownServer(self):
        '''Shutdown remote server with SSH connection.'''
        my_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (self._password, self._password, self._username, self._ipaddr)
        print("server %s poweroff" % self._ipaddr)
        subprocess.run(my_cmd, stdout=subprocess.PIPE, shell=True)


class IPList():
    '''Manage IPs and ports of all servers involved.'''
    def __init__(self, ipFile, currentIP=0, username=USERNAME, password=PASSWD):
        '''Read IPs from a file.'''
        self._currentIP = currentIP
        self._IPs = []
        with open(ipFile, 'r') as f:
            for line in f.readlines():
                if line.strip():
                    self._IPs.append(IP(line.strip()))
                else:
                    break

    def getIPs(self):
        '''Return an list of IPs.'''
        return self._IPs

    def getFullCount(self):
        '''Return the number of containers when all servers are full loaded.'''
        return len(self._IPs) * self._IPs[0].getMaxPayload() if len(self._IPs) else 0

    def getNewPort(self):
        '''
        Get a new rpcPort and a new listenerPort along with the IP addr of a server.
        Return: (IPaddr, rpcPort, listenerPort)
        '''
        if self._currentIP >= len(self._IPs):
            raise ValueError("server overload")
        rpcPort, listenerPort = self._IPs[self._currentIP].getNewPort()
        currentIP = self._IPs[self._currentIP]
        if currentIP.isFullLoaded():
            self._currentIP += 1
        return (currentIP, rpcPort, listenerPort)

    def releaseAll(self):
        self._currentIP = 0

    def stopAllContainers(self):
        '''Stop all containers running on the servers.'''
        threads = []
        for IP in self._IPs:
            t = threading.Thread(target=IP.stopContainers)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
#        for IP in self._IPs:
#            print(IP)
#            IP.execCommand("docker stop $(docker ps --format '{{.Names}}')")


    def startDockerService(self):
        '''Start docker service on all servers.'''
        startTime = time.time()
        CMD = 'echo %s | sudo systemctl start docker' % (PASSWD)
        home = os.path.expanduser('~')
        for ip in self._IPs:
            myCMD = ['ssh-keyscan'] + [ip._ipaddr]
            with open('%s/.ssh/known_hosts' % home, 'a') as outfile:
                subprocess.run(myCMD, stdout=outfile)

        threads = []
        for IP in self._IPs:
            print("%s at %s" % (CMD, IP._ipaddr))
            t = threading.Thread(target=IP.execCommand, args=(CMD,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        endTime = time.time()
        print('start docker service on all servers. elapsed time: %.3fs' % (endTime-startTime))

    def rebootServers(self):
        for IP in self._IPs:
            IP.rebootServer()

    def shutdownServers(self):
        for IP in self._IPs:
            IP.shutdownServer()

def execCommand(cmd, ipaddr, port=22, username=USERNAME, password=PASSWD):
    '''Exec a command on remote server using SSH connection.'''
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ipaddr, port, username, password)
    time.sleep(0.2)
    stdin, stdout, stderr = client.exec_command(cmd)
    time.sleep(0.1)
    if not stderr.read():
        result = stdout.read().strip().decode(encoding='utf-8')
    else:
        result = stderr.read().strip().decode(encoding='utf-8')
    client.close()
    return result

#def stopAll(IP, username=USERNAME, password=PASSWD):
#    '''
#    Stop all running containers on a server.
#    '''
#    ssh = paramiko.SSHClient()
#    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    ssh.connect(hostname=IP, port=22, username=username, password=password)
#    try:
#        NAMES = "docker ps --format '{{.Names}}'"
#        stdin, stdout, stderr = ssh.exec_command(NAMES)
#        result = stdout.read()
#        if result:
#            result = result.decode(encoding='utf-8', errors='strict').split()
#            print(' '.join(result))
#            STOP = 'docker stop %s' % ' '.join(result)
#            stdin, stdout, stderr = ssh.exec_command(STOP)
#            result = stdout.read()
#            if result:
#                print("all nodes at %s stopped" % IP)
#            elif not stderr:
#                print(stderr)
##            return True if result else False
#        elif not stderr:
#            print(stderr)
#    except Exception as e:
#        print('stopAll', e)
#    ssh.close()
#
#def stopAllContainers(IPlist):
#    threads = []
#    for ip in IPlist._ips:
#        print("stop all docker containers at %s" % ip._ip)
#        t = threading.Thread(target=stopAll, args=(ip._ip,))
#        threads.append(t)
#        t.start()
#    for t in threads:
#        t.join()

def shutdownServer(IPlist, username=USERNAME, password=PASSWD):
    '''
    Shutdown all server on IPlist.
    Note: Set param shell=True
    '''
    for ip in IPlist._ips:
        my_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (password, password, username, ip)
        print("server %s poweroff" % ip._ip)
        subprocess.run(my_cmd, stdout=subprocess.PIPE, shell=True)

if __name__ == "__main__":
    f = IPList('ip.txt')
#    for i in range(10):
#        print(f.getNewPort())
#    f.startDockerService()