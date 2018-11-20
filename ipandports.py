#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class IP():
    '''
    Create an IP object with a list of rpc ports and a list of listener ports.
    '''
    def __init__(self, ip, currentPort=0):
        self._maxPayload = 8    # maximum number of clients running on one server
        self._currentPort = currentPort
        self._ip = ip
        self._rpcPorts = range(8515, 8515 + self._maxPayload * 10, 10)
        self._listenerPorts = range(30313, 30313 + self._maxPayload * 10, 10)

    def __repr__(self):
        return self._ip

    def getNewPort(self):
        '''
        Return a tuple of an ECS:(ip, rpcPort, listenerPort).
        '''
        assert self._currentPort < self._maxPayload
        result = (self._ip, self._rpcPorts[self._currentPort], self._listenerPorts[self._currentPort])
        self._currentPort += 1
        return result

    def getMaxPayload(self):
        return self._maxPayload

    def isFullLoaded(self):
        '''
        Decide whether the ECS is full loaded.
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
                self._ips.append(IP(line.rstrip()))

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
        assert self._currentIP < len(self._ips)
        result = self._ips[self._currentIP].getNewPort()
        if self._ips[self._currentIP].isFullLoaded():
            self._currentIP += 1
        return result



if __name__ == "__main__":
    f = IPList('ip.txt')
    ips = f.getIPs()
    for i in range(20):
        print(f.getNewPort())