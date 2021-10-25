#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from chain.const import CONFIG, IP_CONFIG
from chain.hibechain import HIBEChain
# from chain.singlechain import SingleChain
from chain.gethnode import GethNode
from chain.iplist import IPList
from chain.conf import load_config_file
from typing import Optional
from random import randint
from datetime import datetime
import threading
import time

ip_list = IPList(IP_CONFIG)
id_list, thresh_list = load_config_file(CONFIG)
print(id_list)
print(thresh_list)
node_count = sum(n for (n, t) in thresh_list)
print('-----')
print('node_count:', node_count)
print('-----')

# -------------- clear containers -----------------------
ip_list.stop_all_containers()
# ip_list.remove_all_containers()
# -------------------------------------------------------


def get_pf(pf: Optional[list], node: GethNode, pf_list: Optional[list], index: int) -> None:
    try:
        result = node.get_transaction_proof_by_proof(pf)
    except RuntimeError as e:
        time.sleep(0.2)
        result = None
        print(e)
    pf_list[index] = result


start_time = time.time()
hibe = HIBEChain(id_list, thresh_list, ip_list)
hibe.construct_hibe_chain()
connect_time = time.time()

waiting_time = max([chain.node_count for chain in hibe.structured_chains[0]]) // 5
print('another %d seconds waiting for addPeer' % waiting_time)
time.sleep(waiting_time)
if not hibe.is_connected():
    # raise RuntimeError('connection is not ready')
    print('connection is not ready')
else:
    print('connected')

hibe.set_number()
hibe.set_level()
hibe.set_id()


end_time = time.time()
print("connect time %.3fs" % (connect_time-start_time))
set_up_time = end_time - start_time
print("set up time %.3fs" % set_up_time)

root_chain = hibe.get_chain('')
root = root_chain.get_node_by_index(1)

terminal_chains = hibe.structured_chains[-1]
terminal_nodes = [terminal_chain.get_node_by_index(1) for terminal_chain in terminal_chains]
leaf_chains = {hibe.get_chain(terminal_chain.get_parent_chain_id()) for terminal_chain in terminal_chains}
leaf_chains = list(leaf_chains)
leaf_nodes = [leaf_chain.get_node_by_index(1) for leaf_chain in leaf_chains]

time.sleep(hibe.max_level*5)


# ----------------test tps ----------------------

threads = []
for chain in hibe.structured_chains[:-1]:
    for node in chain:
        t = threading.Thread(target=node.start_miner)
        time.sleep(0.02)
        threads.append(t)
        t.start()
for t in threads:
    t.join()

time.sleep(hibe.max_level)

print('number of terminal nodes:', len(terminal_nodes))

# send transactions
print('sending transactions...')
threads = []
for terminal_node in terminal_nodes:
    t = threading.Thread(target=terminal_node.send_transaction3, args=(5721, 1, 0, 1, 10))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

time.sleep(hibe.max_level * 15)
'''
for index, terminal_node in terminal_nodes:
    block_index = 0
    while leaf_nodes[index].get_block_transaction_count(block_index) == 0:
        block_index += 1
        time.sleep(0.2)
    print('-----leaf chain block index is %s-----' % block_index)

    tx_hash = leaf_nodes[index].get_transaction_by_block_number_and_index(block_index, 1)
    
    pf = leaf_nodes[0].get_transaction_proof_by_hash(tx_hash)
    current_chain = leaf_chains[0]
    current_node = leaf_nodes[0]
    current_pf = pf
    
    leaf_chains[0].get_log(leaf_nodes[0].node_index)
    time.sleep(0.5)
    t0 = leaf_chains[0].search_log(leaf_nodes[0].node_index, block_index-1)
    t1 = leaf_chains[0].search_log(leaf_nodes[0].node_index, block_index)
    tps = []
'''



'''
block_index = 1
tx_hash = leaf_node.get_transaction_by_block_number_and_index(block_index, 1)

while not tx_hash:
    block_index += 1
    print('waiting tx hash')
    time.sleep(0.05)
    tx_hash = leaf_node.get_transaction_by_block_number_and_index(block_index, 1)
pf = leaf_node.get_transaction_proof_by_hash(tx_hash)
current_chain = leaf_chain
current_node = leaf_node
current_pf = pf

block_index = 1
leaf_chain.get_log(leaf_node.node_index)
time.sleep(0.5)
leaf_chain.search_log(leaf_node.node_index, block_index)

timestamp_leaf = int(leaf_node.get_block_by_index(1)['timestamp'], 16)
for i in range(hibe.max_level-1):
    current_chain = hibe.get_chain(current_chain.get_parent_chain_id())
    # threads = []
    # pf_list = [None] * current_chain.node_count
    # while sum([True if pf else False for pf in pf_list]) < current_chain.threshold:
    #     # if sum([True if pf else False for pf in pf_list]) <= current_chain.threshold // 3:
    #     #     time.sleep(10)
    #     # elif sum([True if pf else False for pf in pf_list]) <= current_chain.threshold // 2:
    #     #     time.sleep(5)
    #     for index, node in enumerate(current_chain.nodes):
    #         if not pf_list[index]:
    #             t = threading.Thread(target=get_pf, args=(current_pf, node, pf_list, index))
    #             t.start()
    #             threads.append(t)
    #     for t in threads:
    #         t.join()
    # for i in range(current_chain.node_count):
    #     if pf_list[i]:
    #         current_pf = pf_list[i]
    #         break
    while True:
        try:
            search_index = randint(1, current_chain.node_count)
            print(search_index)
            current_node = current_chain.get_node_by_index(search_index)
            tmp_pf = current_node.get_transaction_proof_by_proof(current_pf)
            if tmp_pf:
                block_index = int(tmp_pf[-1], 16)
                print('block index is %d.' % block_index)

                current_chain.get_log(current_node.node_index)
                time.sleep(0.5)
                current_chain.search_log(current_node.node_index, block_index)

                timestamp_current = current_node.get_block_by_index(block_index)['timestamp']
                tmp_pf = tmp_pf[:-1]
                break
        except RuntimeError as e:
            time.sleep(15)
            print(e)
    current_pf = tmp_pf

end_time = time.time()

timestamp_root = int(root.get_block_by_index(block_index)['timestamp'], 16)

latency = (datetime.fromtimestamp(timestamp_root) - datetime.fromtimestamp(timestamp_leaf)).seconds


# hibe.destruct_hibe_chain()
print(current_pf)
print(current_chain.chain_id)
search_time = end_time - sent_time
print('search time: ', search_time)
print('latency:', latency)
with open('elapsed_time.txt', 'a') as log:
    log.write(time.asctime())
    log.write('\n'.join(id_list))
    log.write('\n')
    log.write(', '.join(map(str, thresh_list)))
    log.write('\n')
    log.write('set up time: %.6f\n' % set_up_time)
    log.write('search time: %.6f\n' % search_time)
    log.write('latency: %d\n\n' % latency)
'''
# ----------------test latency end --------------------

# ----------------remove all containers ---------------
#
# ip_list.stop_all_containers()
# time.sleep(0.2)
# ip_list.remove_all_containers()
