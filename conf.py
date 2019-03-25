#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 11:04:55 2019

@author: rkd
"""

import json
from math import ceil

def genTestCfg(level=3, cfgFile='conf0.txt'):
    chainCount = 2 ** (level + 1) - 1
    IDList = [None] * chainCount
    IDList[0] = ''
    threshList = [(20, 16)]
    for i in range(1, chainCount):
        if i % 2:
            IDList[i] = IDList[ceil(i/2)-1] + '0001'
        else:
            IDList[i] = IDList[ceil(i/2)-1] + '0002'
        threshList.append((20, 16))
    newCount = chainCount

    for i in range(chainCount//2, chainCount):
        for j in range(1, 9):
            IDList.append(IDList[i]+'%04d' % j)
            threshList.append((1,1))
            newCount += 1
        break
    print(IDList)
    print(threshList)
    chainCount = newCount

    lines = []
    for i in range(level+1):
        index = 2 ** i
        tmpID = ' '.join(IDList[:index])
        tmpThresh = ' '.join('%s,%s' % tup for tup in threshList[:index])
        IDList = IDList[index:]
        threshList = threshList[index:]
        lines.append(tmpID)
        lines.append(tmpThresh)
    tmpID = ' '.join(IDList)
    tmpThresh = ' '.join('%s,%s' % tup for tup in threshList)
    lines.append(tmpID)
    lines.append(tmpThresh)
    with open(cfgFile, 'w') as file:
        file.write('\n'.join(lines))

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

#    for i in range(0, 5):
#        for j in range(0, 10):
#            for k in range(0, 10):
#                for l in range(0, 10):
#                    ac = hex(ord(str(i)))[2:] + hex(ord(str(j)))[2:] + hex(ord(str(k)))[2:] + hex(ord(str(l)))[2:] + '0' * 31 + '1'
#                    genesis['alloc'][ac] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}

    newGenesis = json.dumps(genesis, indent=2)
    with open('docker/%s' % cfgFile, 'w') as f:
        print(newGenesis, file=f)

def confTerminals(cfgFile, terminals):
    with open('docker/%s' % cfgFile, 'rb') as f:
        genesis = json.load(f)
    for chain in terminals:
        account = []
        for char in chain._id:
            account.append(hex(ord(char))[2:])
        acc = ''.join(account)
        acc = acc + (40 - len(acc) - 1) * '0' + '1'
        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
    newGenesis = json.dumps(genesis, indent=2)
    with open('docker/%s' % cfgFile, 'w') as f:
        print(newGenesis, file=f)

if __name__ == '__main__':
    IDList, threshList = loadCfg()
    print(IDList)
    print(threshList)
    genTestCfg()
