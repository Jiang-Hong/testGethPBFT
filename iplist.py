#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko
import threading
import time
import subprocess
import os

USERNAME = 'u0'  # username of servers
PASSWD = 'test'  # password of servers
MAXPAYLOAD = 20  # maximum number of containers running on one server


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
        '''
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self._ipaddr, port, self._username, self._password)
            time.sleep(0.2)
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
            time.sleep(0.1)
            out = stdout.read().strip().decode(encoding='utf-8')
            err = stderr.read().strip().decode(encoding='utf-8')
            if not err:
                result = out
                return result
            else:
                result = err
                if result:
                    print('-------------')
                    print(cmd)
                    print(result)
                    print('-------------')
                    raise RuntimeError("exec command error: %s" % cmd)

    def isDockerRunning(self):
        '''Check if docker service is running on specified ip.'''
        CMD = 'systemctl is-active docker'
        result = self.execCommand(CMD)
        return True if result == 'active' else False

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
        my_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo reboot' % (
            self._password, self._password, self._username, self._ipaddr)
        print("server %s reboot" % self._ipaddr)
        subprocess.run(my_cmd, stdout=subprocess.PIPE, shell=True)

    def shutdownServer(self):
        '''Shutdown remote server with SSH connection.'''
        my_cmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (
            self._password, self._password, self._username, self._ipaddr)
        print("server %s poweroff" % self._ipaddr)
        subprocess.run(my_cmd, stdout=subprocess.PIPE, shell=True)


class IPList():
    '''Manage IPs and ports of all servers involved.'''

    def __init__(self, ipFile, currentIP=0, username=USERNAME, password=PASSWD):
        '''Read IPs from a file.'''
        self._currentIP = currentIP
        self._IPs = []
        self._ifInit = False
        with open(ipFile, 'r') as f:
            for line in f.readlines():
                if line.strip():
                    self._IPs.append(IP(line.strip()))
                else:
                    break
        self._initService()

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

    def _initService(self):
        '''
        Add key to know_hosts file.
        Start docker service on all servers.
        '''
        startTime = time.time()
        known_hosts = os.path.expanduser('~/.ssh/known_hosts')
        keys = paramiko.hostkeys.HostKeys(filename=known_hosts)

        # get results from multi-threading
        # def _threadResult(IP, results, index):
        #     results[index] = keys.lookup(IP._ipaddr)
        def _threadResult(IP, results, index): return results.setdefault(str(index), keys.lookup((IP._ipaddr)))

        length = len(self._IPs)
        threads = []
        results = {}
        for n, IP in enumerate(self._IPs):
            # use multi-threading to lookup keys
            t = threading.Thread(target=_threadResult, args=(IP, results, str(n)))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # add keys to known_hosts one by one
        for i in range(length):
            if not results.get(str(i)):
                print('%s is not in know_hosts. Adding to known_hosts' % self._IPs[i])
                myCMD = 'ssh-keyscan %s' % self._IPs[i]._ipaddr
                with open(known_hosts, 'a') as outfile:
                    subprocess.run(myCMD, stdout=outfile, shell=True)

        CMD = 'echo %s | sudo -S systemctl start docker' % PASSWD
        print('starting docker service on all services')
        threads = []
        for IP in self._IPs:
            t = threading.Thread(target=IP.execCommand, args=(CMD,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        endTime = time.time()
        print('initService elapsed time: %.3fs' % (endTime - startTime))

    def rebootServers(self):
        for IP in self._IPs:
            IP.rebootServer()

    def shutdownServers(self):
        for IP in self._IPs:
            IP.shutdownServer()


def execCommand(cmd, ipaddr, port=22, username=USERNAME, password=PASSWD):
    '''Exec a command on remote server using SSH connection.'''
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ipaddr, port, username, password)
        time.sleep(0.2)
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        time.sleep(0.1)
        out = stdout.read().strip().decode(encoding='utf-8')
        err = stderr.read().strip().decode(encoding='utf-8')
        if not err:
            result = out
        else:
            result = err
    return result


# def stopAll(IP, username=USERNAME, password=PASSWD):
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
# def stopAllContainers(IPlist):
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
    for IP in IPlist._ips:
        myCmd = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo shutdown now' % (password, password, username, IP)
        print("server %s poweroff" % IP._ip)
        subprocess.run(myCmd, stdout=subprocess.PIPE, shell=True)


def setUlimit(IPlist, username=USERNAME, password=PASSWD):
    '''Change ulimit value for servers.'''
    for IP in IPlist._IPs:
        subprocess.run(['sshpass -p %s scp setUlimit.sh %s@%s:' % (IP._password, IP._username, IP._ipaddr)],
                       stdout=subprocess.PIPE, shell=True)
        CMDChmod = 'sshpass -p %s ssh -tt %s@%s chmod +x setUlimit.sh' % (IP._password, IP._username, IP._ipaddr)
        CMDExec = 'echo %s | sshpass -p %s ssh -tt %s@%s sudo ./setUlimit.sh' % (
            IP._password, IP._password, IP._username, IP._ipaddr)
        print('set nopro and nofile')
        subprocess.run(CMDChmod, stdout=subprocess.PIPE, shell=True)
        subprocess.run(CMDExec, stdout=subprocess.PIPE, shell=True)


# def test(IPlist, username=USERNAME, password=PASSWD):
#     for IP in IPlist._IPs:
#         subprocess.run('echo $HOME', shell=True)


if __name__ == "__main__":
    f = IPList('ip.txt')
#    for i in range(10):
#        print(f.getNewPort())
#    f.initService()
