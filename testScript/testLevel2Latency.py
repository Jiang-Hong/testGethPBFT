#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from chain.const import CONFIG, IP_CONFIG
from chain.hibechain import HIBEChain
from chain.gethnode import GethNode
from chain.iplist import IPList
from chain.conf import load_config_file
from typing import Optional
from datetime import datetime
import threading
import time
import json
import subprocess

# SEND_TX_SPEED = 120

for level in range(5, 6):    # number of levels
    for _ in range(1):    # iter round
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

        sent_time = datetime.utcnow()
        terminal_node.send_transaction3(valid_keys, 1, 0, 1, 10)

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
            time.sleep(0.2)
            leaf_chain.search_log(leaf_node.node_index, block_index)
            time.sleep(0.2)
            with open('../data/chain%s_node%d.json' % (leaf_chain.chain_id, leaf_node.node_index), 'rb') as f:
                block_data = json.load(f)
                try:
                    prepare_time = datetime.strptime(block_data[str(block_index)]['prepare'],
                                                     '%Y-%m-%d-%H:%M:%S.%f') - sent_time
                    consensus_time = datetime.strptime(block_data[str(block_index)]['consensus'],
                                                       '%Y-%m-%d-%H:%M:%S.%f') - sent_time
                    written_time = datetime.strptime(block_data[str(block_index)]['written'],
                                                     '%Y-%m-%d-%H:%M:%S.%f') - sent_time
                except KeyError as e:
                    with open('../result/elapsed_time.txt', 'a') as log:
                        log.write('%s chain%s_node%d\n' % (e, current_chain.chain_id, current_node.node_index))
                    time.sleep(0.5)

            with open('../result/level2latency.txt'+str(datetime.utcnow().date()), 'a') as f:
                f.write('%s,%s,%s,%d,%d\n' % (prepare_time, consensus_time, written_time,
                                              leaf_chain.level, block_index))

        while current_chain.chain_id != '':
            try:
                current_chain = hibe.get_chain(current_chain.get_parent_chain_id())
                tmp_pf = current_chain.get_node_by_index(1).get_transaction_proof_by_proof(current_pf)
                if tmp_pf:
                    block_index = int(tmp_pf[-1], 16)
                    print('block index is %d.' % block_index)

                for current_node in current_chain.nodes:
                    current_chain.get_log(current_node.node_index)
                    time.sleep(0.2)
                    current_chain.search_log(current_node.node_index, block_index)
                    time.sleep(0.2)
                    with open('../data/chain%s_node%d.json' % (current_chain.chain_id, current_node.node_index), 'rb') as f:
                        block_data = json.load(f)
                        try:
                            prepare_time = datetime.strptime(block_data[str(block_index)]['prepare'],
                                                             '%Y-%m-%d-%H:%M:%S.%f') - sent_time
                            consensus_time = datetime.strptime(block_data[str(block_index)]['consensus'],
                                                               '%Y-%m-%d-%H:%M:%S.%f') - sent_time
                            written_time = datetime.strptime(block_data[str(block_index)]['written'],
                                                             '%Y-%m-%d-%H:%M:%S.%f') - sent_time
                        except KeyError as e:
                            with open('../result/elapsed_time.txt', 'a') as log:
                                log.write('%s chain%s_node%d\n' % (e, current_chain.chain_id, current_node.node_index))
                            time.sleep(0.5)

                    with open('../result/level2latency.txt'+str(datetime.utcnow().date()), 'a') as f:
                        f.write('%s,%s,%s,%d,%d\n' % (prepare_time, consensus_time, written_time,
                                                      current_chain.level, block_index))
                current_pf = tmp_pf[:-1]
            except RuntimeError as e:
                with open('../result/elapsed_time.txt', 'a') as log:
                    log.write('miss\n')
                time.sleep(2)
                print(e)
        hibe.stop_miner()


