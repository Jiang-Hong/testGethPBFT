#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import CONFIG, IP_CONFIG
from hibechain import HIBEChain
from iplist import IPList
from conf import load_config_file
import time

ip_list = IPList(IP_CONFIG)
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

# key_count = terminal_node.key_count()
#
# while True:
#     time.sleep(5)
#     tmp_count = terminal_node.key_count()
#     if tmp_count != 0 and tmp_count == key_count:
#         break
#     key_count = tmp_count
#
# time.sleep(5)

#
# time.sleep(MAXPAYLOAD * 15)
#
# nonce = 0
# terminal_node.send_transaction3(7500, 1, nonce, value=nonce+1)
# time.sleep(5)
# while leaf_node.txpool_status() == 0:
#     time.sleep(5)
#     print('sending transactions...')
#     nonce += 1
#     terminal_node.send_transaction3(6000, 1, nonce, value=nonce+1)
#     if nonce == 100:
#         raise RuntimeError('sending transactions error')
#
# for node in leaf_chain.nodes:
#     node.start_miner()
#
# time.sleep(20)
#
# for i in range(1, 20):
#     x = leaf_node.get_block_transaction_count(i)
#     if x:
#         print('-----------------------------', i, x)
#
