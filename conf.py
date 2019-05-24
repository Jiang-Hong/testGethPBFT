#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 11:04:55 2019

@author: rkd
"""

import json
import time
from math import ceil


def generate_test_config(level: int =3, terminal_count: int = 8, config_file: str = 'conf0.txt') -> None:
    """Generate a HIBEChain config file."""
    if level > 9:    # level starts from 0
        raise ValueError("level number should not exceeds 9")
    chain_count = 2 ** (level + 1) - 1
    id_list = [None] * chain_count
    id_list[0] = ''
    thresh_list = [(21, 18)]
    for i in range(1, chain_count):
        if i % 2:
            id_list[i] = id_list[ceil(i/2)-1] + '01'
        else:
            id_list[i] = id_list[ceil(i/2)-1] + '02'
        thresh_list.append((20, 17))
    new_count = chain_count

    for i in range(chain_count//2, chain_count):
        for j in range(1, terminal_count+1):
            id_list.append(id_list[i]+'%04d' % j)
            thresh_list.append((1, 1))
            new_count += 1
        break
    print('Total: %d nodes' % sum([x for x, _ in thresh_list]))
    print(id_list)
    print(thresh_list)
    # chain_count = new_count

    lines = []
    for i in range(level+1):
        index = 2 ** i
        tmp_id = ' '.join(id_list[:index])
        tmp_thresh = ' '.join('%s,%s' % tup for tup in thresh_list[:index])
        id_list = id_list[index:]
        thresh_list = thresh_list[index:]
        lines.append(tmp_id)
        lines.append(tmp_thresh)
    tmp_id = ' '.join(id_list)
    tmp_thresh = ' '.join('%s,%s' % tup for tup in thresh_list)
    lines.append(tmp_id)
    lines.append(tmp_thresh)
    with open(config_file, 'w') as file:
        file.write('\n'.join(lines))


def generate__tri_test_config(level: int = 3, terminal_count: int = 8, config_file: str = 'conf0.txt') -> None:
    """Generate a HIBEChain config file."""
    if level > 3:    # level starts from 0
        raise ValueError("level number should not exceeds 3")
    chain_count = (3 ** (level + 1) - 1) // 2
    id_list = [None] * chain_count
    id_list[0] = ''
    thresh_list = [(21, 18)]
    for i in range(1, chain_count):
        if i % 3 == 1:
            id_list[i] = id_list[ceil(i/3)-1] + '0001'
        elif i % 3 == 2:
            id_list[i] = id_list[ceil(i/3)-1] + '0002'
        else:
            id_list[i] = id_list[ceil(i/3)-1] + '0003'
        thresh_list.append((16, 14))
    new_count = chain_count

    for i in range(chain_count//3, chain_count):
        for j in range(1, terminal_count+1):
            id_list.append(id_list[i]+'%04d' % j)
            thresh_list.append((1, 1))
            new_count += 1
        break
    print('Total: %d nodes' % sum([x for x, _ in thresh_list]))
    print(id_list)
    print(thresh_list)
    # chain_count = new_count

    lines = []
    for i in range(level+1):
        index = 3 ** i
        tmp_id = ' '.join(id_list[:index])
        tmp_thresh = ' '.join('%s,%s' % tup for tup in thresh_list[:index])
        id_list = id_list[index:]
        thresh_list = thresh_list[index:]
        lines.append(tmp_id)
        lines.append(tmp_thresh)
    tmp_id = ' '.join(id_list)
    tmp_thresh = ' '.join('%s,%s' % tup for tup in thresh_list)
    lines.append(tmp_id)
    lines.append(tmp_thresh)
    with open(config_file, 'w') as file:
        file.write('\n'.join(lines))


def load_config_file(config_file: str = 'conf0.txt') -> tuple:
    """Get id_list & thresh_list from a config file."""
    id_list = ['']
    thresh_list = []
    with open(config_file) as file:
        lines = file.readlines()
        while not lines[-1].split():
            lines.pop(-1)
        if len(lines) % 2:
            raise RuntimeError('line number of configure file should be even')
        while True:
            add_id = lines[0]
            thresh = lines[1]
            lines = lines[2:]
            id_list += add_id.split()
            thresh_list += list(map(tuple, [item.split(',') for item in thresh.split()]))
            if not lines:
                break
    thresh_list = [tuple(map(int, thresh)) for thresh in thresh_list]
    if len(id_list) != len(thresh_list):
        raise RuntimeError('length of id_list should match length of thresh_list')
    return id_list, thresh_list


def generate_genesis(chain_id: int, accounts: list, config_file: str) -> None:
    """Generate a genesis file."""
    with open('docker/120.json', 'rb') as f:
        genesis = json.load(f)
    genesis['config']['chainId'] = chain_id

    for acc in accounts:
        genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
    extra_data = '0x' + '0'*64 + ''.join(accounts) + '0' * 130
    print("extra data in genesis file", extra_data)
    genesis['extraData'] = extra_data

    new_genesis = json.dumps(genesis, indent=2)
    with open('docker/%s' % config_file, 'w') as f:
        print(new_genesis, file=f)
    time.sleep(0.05)

def generate_leaf_genesis(config_file: str, leaves: list) -> None:
    """Generate a genesis file for leaf chains and terminals."""
    with open('docker/%s' % config_file, 'rb') as f:
        genesis = json.load(f)

    for chain in leaves:
        print('--------------leaf-------------------------------')
        print('-------------file name', config_file)
        account_ascii = []
        terminal_id = chain.chain_id[:-2]
        for char in terminal_id:
            account_ascii.append(hex(ord(char))[2:])
        tmp_account = ''.join(account_ascii)
        for i in range(0, 2):
            for j in range(0, 256):
                terminal_account = tmp_account
                terminal_account += hex(i)[2:].zfill(2) + hex(j)[2:].zfill(2)
                terminal_account = terminal_account + (40 - len(terminal_account) - 1) * '0' + '1'
                # print(terminal_account)
                if len(terminal_account) != 40:
                    print('terminal account:', terminal_account)
                    raise ValueError('length of account should be 40')
                genesis['alloc'][terminal_account] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
        new_genesis = json.dumps(genesis, indent=2)
        with open('docker/%s' % config_file, 'w') as f:
            print(new_genesis, file=f)
        time.sleep(0.05)

# def generate_terminal_genesis(config_file, terminals):
#     """Generate a genesis file for leaf chains and terminals."""
#     with open('docker/%s' % config_file, 'rb') as f:
#         genesis = json.load(f)
#     for chain in terminals:
#         account = []
#         for char in chain.chain_id:
#             account.append(hex(ord(char))[2:])
#         acc = ''.join(account)
#         acc = acc + (40 - len(acc) - 1) * '0' + '1'
#         if len(acc) != 40:
#             print('account:', acc)
#             raise ValueError('length of account should be 40')
#         print(acc)
#         genesis['alloc'][acc] = {'balance': "0x200000000000000000000000000000000000000000000000000000000000000"}
#     new_genesis = json.dumps(genesis, indent=2)
#     with open('docker/%s' % config_file, 'w') as f:
#         print(new_genesis, file=f)


if __name__ == '__main__':
    id_list, thresh_list = load_config_file()
    print(id_list)
    print(thresh_list)
    generate_test_config()
