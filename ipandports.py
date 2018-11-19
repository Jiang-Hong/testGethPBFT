#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class IP():
    def __init__(self, ip, currentPort=0):
        self._maxPayload = 7
        self._currentPort = currentPort
        self._ip = ip
        self._rpcPorts = range(8515, 8515 + self._maxPayload * 10, 10)
        self._listenerPorts = range(30313, 30313 + self._maxPayload * 10, 10)

    def __repr__(self):
        return self._ip

    def getUnusedPort(self):
        assert self._currentPayload < self._maxPayload
        result = (self._ip, self._rpcPorts[self._currentPayload], self._listenerPorts[self._currentPayload])
        self._currentPayload += 1
        return result

    def isFull(self):
        return self._currentPayload >= self._maxPayload

    def releaseAll(self):
        self._currentPayload = 0


class IPList():
    def __init__(self, ipFile):
        self._currentIP = 0
        self._currentPort = 0
        self._ips = []
        with open(ipFile, 'r') as f:
            for line in f.readlines():
                self._ips.append(IP(line.rstrip()))

    def getIPs(self):
        return self._ips



if __name__ == "__main__":
    f = IPList('ip.txt')
    ips = f.getIPs()
    for ip in ips:
        print(ip.getUnusedPort())