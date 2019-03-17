#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 11:04:55 2019

@author: rkd
"""

import json

def genCfg(cfgFile='conf.txt'):
    pass

def loadCfg(cfgFile='conf.txt'):
    IDList = ['']
    threshList = []
    with open(cfgFile) as file:
        lines = file.readlines()
        while not lines[-1].split():
            lines.pop(-1)
        if len(lines) % 2:
            raise RuntimeError('line number of configure file should be even')
        while True:
            ID = lines[0]
            thresh = lines[1]
            lines = lines[2:]
            IDList += ID.split()
            threshList += list(map(tuple, [item.split(',') for item in thresh.split()]))
            if not lines:
                break
    threshList = [tuple(map(int, thresh)) for thresh in threshList]
    if len(IDList) != len(threshList):
        raise RuntimeError('length of IDList should match length of threshList')
    return IDList, threshList

def confGenesis(chainId, accounts, cfgFile):
    with open('docker/120.json', 'rb') as f:
        genesis = json.load(f)
    genesis['config']['chainId'] = chainId

    for acc in accounts:
        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
    extradata = '0x' + '0'*64 + ''.join(accounts) + '0' * 130
    print("extra data in genesis file", extradata)
    genesis['extraData'] = extradata
#    print(genesis) #

    for i in range(0, 5):
        for j in range(0, 10):
            for k in range(0, 10):
                for l in range(0, 10):
                    ac = hex(ord(str(i)))[2:] + hex(ord(str(j)))[2:] + hex(ord(str(k)))[2:] + hex(ord(str(l)))[2:] + '0' * 31 + '1'
#                    print(ac)
                    genesis['alloc'][ac] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}

    newGenesis = json.dumps(genesis, indent=2)
    with open('docker/%s' % cfgFile, 'w') as f:
        print(newGenesis, file=f)

#def confTerminals(terminals, cfgFile):
#    with open('docker/%s' % cfgFile, 'rb') as f:
#        genesis = json.load(f)
#    for chain in terminals:
#        account = []
#        for char in chain._id:
#            account.append(hex(ord(char))[2:])
#        acc = ''.join(account)
#        acc = acc + (40 - len(acc) - 1) * '0' + '1'
#        print(acc)
#        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
#    newGenesis = json.dumps(genesis, indent=2)
#    with open('docker/%s' % cfgFile, 'w') as f:
#        print(newGenesis, file=f)

if __name__ == '__main__':
    IDList, threshList = loadCfg()
    print(IDList)
    print(threshList)
