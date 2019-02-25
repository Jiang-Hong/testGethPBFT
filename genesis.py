#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json

def confGenesis(chainId, accounts):
    with open('docker/120.json', 'rb') as f:
        genesis = json.loads(f.read())
    genesis['config']['chainId'] = chainId

    for acc in accounts:
        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
    extradata = '0x' + '0'*64 + ''.join(accounts) + '0' * 130
    print(extradata)
    genesis['extraData'] = extradata
#    print(genesis) #
    newGenesis = json.dumps(genesis, indent=2)
    with open('docker/%s.json' % str(chainId), 'w') as f:
        print(newGenesis, file=f)

def confTerminals(terminals, cfgFile):
    with open('docker/%s' % cfgFile, 'rb') as f:
        genesis = json.loads(f.read())
    for chain in terminals:
        account = []
        for char in chain._id:
            account.append(hex(ord(char))[2:])
        acc = ''.join(account)
        acc = acc + (40 - len(acc) - 1) * '0' + '1'
        print(acc)
        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
    newGenesis = json.dumps(genesis, indent=2)
    with open('docker/%s' % cfgFile, 'w') as f:
        print(newGenesis, file=f)