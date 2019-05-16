#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import CONFIG
from hibechain import HIBEChain
from iplist import IPList
from conf import load_config_file
import time

ip_list = IPList('ip.txt')
id_list, thresh_list = load_config_file(CONFIG)
print(id_list)
print(thresh_list)
node_count = sum(n for (n, t) in thresh_list)
print('-----')
print('node_count:', node_count)
print('-----')

start_time = time.time()
hibe = HIBEChain(id_list, thresh_list, ip_list)
hibe.construct_hibe_chain()
connect_time = time.time()


print('another %s seconds waiting for addPeer' % str(10))
time.sleep(10)

hibe.set_number()
hibe.set_level()
hibe.set_id()


end_time = time.time()
print("connect time %.3fs" % (connect_time-start_time))
print("set up time %.3fs" % (end_time-start_time))

root_chain = hibe.get_chain('')
root = root_chain.get_node_by_index(1)

terminal_chain = hibe.get_chain(hibe.structured_chains[-1][0].chain_id)
terminal_node = terminal_chain.get_node_by_index(1)

leaf_chain = hibe.get_chain(terminal_chain.get_parent_chain_id())
leaf_node = leaf_chain.get_node_by_index(1)

key_count = terminal_node.key_count()

while True:
    time.sleep(5)
    tmp_count = terminal_node.key_count()
    if tmp_count != 0 and tmp_count == key_count:
        break
    key_count = tmp_count

time.sleep(5)


# ----------------test latency ----------------------

for chain in hibe.structured_chains[:-2]:
    for node in chain:
        node.start_miner()

terminal_node.send_transaction3(100, 1, 0, 1)

for node in hibe.structured_chains[-2]:
    node.start_miner()

sent_time = time.time()

tx_hash = leaf_node.get_transaction_by_block_number_and_index(1, 1)
while not tx_hash:
    tx_hash = leaf_node.get_transaction_by_block_number_and_index(1, 1)
    time.sleep(0.05)
pf = leaf_node.get_transaction_proof_by_hash(tx_hash)
current_chain = leaf_chain
current_node = leaf_node
current_pf = pf
for i in range(hibe.max_level-1):
    current_chain = hibe.get_chain(current_chain.get_parent_chain_id())
    current_node = current_chain.get_node_by_index(1)
    while True:
        try:
            tmp_pf = current_node.get_transaction_proof_by_proof(current_pf)
            if tmp_pf:
                break
        except RuntimeError as e:
            time.sleep(0.05)
    current_pf = tmp_pf
end_time = time.time()
print(current_pf)
print(current_chain.chain_id)
print('search time: ', end_time - sent_time)

# ----------------test latency end --------------------
