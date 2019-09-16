#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.const import CONFIG, IP_CONFIG
from src.hibechain import HIBEChain
from src.gethnode import GethNode
from src.iplist import IPList
from src.conf import load_config_file
from typing import Optional
from datetime import datetime
import threading
import time
import subprocess

# SEND_TX_SPEED = 120

for level in range(1, 2):    # number of levels
    for round in range(1):    # iter round
        # generate id_list and thresh_list
        id_list = [""]
        thresh_list = [(1, 1)]
        ip_list = IPList(IP_CONFIG)
        for m in range(1, level+1):
            new_level_id = '01' * m
            id_list.append(new_level_id)
            thresh_list = [(19, 13)] + thresh_list
        print(id_list)
        print(thresh_list)
        node_count = sum(n for (n, t) in thresh_list)
        print('-----')
        print('node_count:', node_count)
        print('-----')

        # -------------- clear containers -----------------------
        ip_list.stop_all_containers()
        print('-----')
        print()

        # ---------------- set up -------------------------------
        start_time = time.time()
        hibe = HIBEChain(id_list, thresh_list, ip_list)
        hibe.construct_hibe_chain()
        connect_time = time.time()

        hibe.set_number()
        hibe.set_level()
        hibe.set_id()

        end_time = time.time()
        print("connect time %.3fs" % (connect_time-start_time))
        set_up_time = end_time - start_time
        print("total set up time %.3fs" % set_up_time)

        terminal_chains = hibe.structured_chains[-1]
        terminal_chain = terminal_chains[0]
        # terminal_nodes = [terminal_chain.get_node_by_index(1) for terminal_chain in terminal_chains]
        terminal_node = terminal_chain.get_node_by_index(1)

        # leaf_chains = {hibe.get_chain(terminal_chain.get_parent_chain_id()) for terminal_chain in terminal_chains}
        # leaf_chains = list(leaf_chains)
        leaf_chain = hibe.get_chain(terminal_chain.get_parent_chain_id())
        # leaf_nodes = [leaf_chain.get_node_by_index(1) for leaf_chain in leaf_chains]

        # ----------------test latency ----------------------
        hibe.start_miner()
        time.sleep(2)
        valid_keys = terminal_node.key_count()

        terminal_node.send_transaction3(valid_keys, 1, 0, 1, 10)
        sent_time = datetime.utcnow()

        print('waiting...')
        time.sleep(hibe.max_level*60)
        print('start')

        # clear data folder
        subprocess.run('rm ../data/*', shell=True)

        block_index = 1
        leaf1 = leaf_chain.get_node_by_index(1)    # leaf1 is the node in leaf chain with index 1
        while leaf1.get_block_transaction_count(block_index) == 0:
            block_index += 1
            time.sleep(0.2)
        with open('../result/path%s.txt' % round, 'a') as search_path:
            search_path.write('sent_time is %s\n' % sent_time)
            search_path.write('leaf chain block index is %d\n' % block_index)

        tx_index = 1
        tx_count = leaf1.get_block_transaction_count(block_index)
        tx_hash = leaf1.get_transaction_by_block_number_and_index(block_index, tx_index)

        while not tx_hash and tx_index < tx_count:
            tx_index += 1
            print('waiting tx hash')
            time.sleep(0.05)
        tx_hash = leaf1.get_transaction_by_block_number_and_index(block_index, tx_index)
        pf = leaf1.get_transaction_proof_by_hash(tx_hash)

        current_chain = leaf_chain
        current_node = leaf1
        current_pf = pf

        for leaf_node in leaf_chain.nodes:
            leaf_chain.get_log(leaf_node.node_index)
            time.sleep(0.5)
            leaf_chain.search_log(leaf_node.node_index, block_index-1)
            leaf_chain.search_log(leaf_node.node_index, block_index)

'''

# timestamp_leaf = int(n0.get_block_by_index(1)['timestamp'], 16)
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
            for search_index in range(1, current_chain.node_count+1):
                # search_index = randint(1, current_chain.node_count)
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
            current_pf = tmp_pf
            break

        except RuntimeError as e:
            with open('data/elapsed_time.txt', 'a') as log:
                log.write('miss\n')
            time.sleep(20)
            print(e)

end_time = time.time()

timestamp_root = int(root.get_block_by_index(block_index)['timestamp'], 16)

latency = (datetime.fromtimestamp(timestamp_root) - datetime.fromtimestamp(timestamp_leaf)).seconds


# hibe.destruct_hibe_chain()
# print(current_pf)
print(current_chain.chain_id)
search_time = end_time - sent_time
print('search time: ', search_time)
print('latency:', latency)
with open('data/elapsed_time.txt', 'a') as log:
    log.write(time.asctime())
    log.write(', '.join(id_list))
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

