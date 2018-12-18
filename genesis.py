#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json

with open('docker/10.json', 'rb') as f:
    genesis = json.loads(f.read())
genesis['config']['chainId'] = 101

newGenesis = json.dumps(genesis, indent=2)
with open('docker/new.json', 'w') as f:
    print(newGenesis, file=f)