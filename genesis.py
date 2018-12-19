#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json

def confGenesis(chainId, accounts):
    with open('docker/120.json', 'rb') as f:
        genesis = json.loads(f.read())
    genesis['config']['chainId'] = chainId

    for acc in accounts:
        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
    print(genesis) #
    newGenesis = json.dumps(genesis, indent=2)
    with open('docker/%s.json' % str(chainId), 'w') as f:
        print(newGenesis, file=f)