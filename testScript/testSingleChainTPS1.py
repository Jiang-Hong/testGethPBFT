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


for i0 in range(7, 11):
    SEND_TX_SPEED = i0 * 5
    for _ in range(2):
        ip_list = IPList(IP_CONFIG)
        thresh_list = [(4, 3), (1, 1)]
        # id_list, thresh_list = load_config_file(CONFIG)
        id_list = ["", "01"]

        print(id_list)
        print(thresh_list)
        node_count = sum(n for (n, t) in thresh_list)
        print('-----')
        print('node_count:', node_count)
        print('-----')

        # -------------- clear containers -----------------------
        ip_list.stop_all_containers()
        # ip_list.remove_all_containers()
        print('-----')
        print()
        # -------------------------------------------------------


        start_time = time.time()
        hibe = HIBEChain(id_list, thresh_list, ip_list)
        hibe.construct_hibe_chain()
        connect_time = time.time()

        hibe.set_number()
        hibe.set_level()
        hibe.set_id()

        setup_end_time = time.time()
        print("connect time %.3fs" % (connect_time-start_time))
        set_up_time = setup_end_time - start_time
        print("set up time %.3fs" % set_up_time)

        root_chain = hibe.get_chain('')
        root = root_chain.get_node_by_index(1)

        terminal_chains = hibe.structured_chains[-1]
        terminal_nodes = [terminal_chain.get_node_by_index(1) for terminal_chain in terminal_chains]
        leaf_chains = {hibe.get_chain(terminal_chain.get_parent_chain_id()) for terminal_chain in terminal_chains}
        leaf_chains = list(leaf_chains)
        # leaf_nodes = [leaf_chain.get_node_by_index(1) for leaf_chain in leaf_chains]

        key_count = [terminal_node.key_count() for terminal_node in terminal_nodes]

        time.sleep(hibe.max_level*5)

        # ----------------test latency ----------------------

        threads = []
        for chain in hibe.structured_chains[:-1]:
            for node in chain:
                t = threading.Thread(target=node.start_miner)
                t.start()
                threads.append(t)
                time.sleep(0.02)
        for t in threads:
            t.join()

        time.sleep(1)

        # --------------------------------------------------------
        iter_round = 1
        transaction_sent_number = 60 * SEND_TX_SPEED
        transaction_sent_speed = SEND_TX_SPEED

        threads = []
        for terminal_node in terminal_nodes:
            t = threading.Thread(target=terminal_node.send_transaction3, args=(transaction_sent_number, iter_round,
                                                                               0, 1, transaction_sent_speed))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        print('waiting...')
        time.sleep(hibe.max_level*30)  # cannot be too small in case of insufficient data
        print('start')

        # clear data folder
        subprocess.run('rm ../data/*', shell=True)

        sent_time = time.time()

        for leaf_chain in leaf_chains:
            block_index = 0
            tx_index = 0
            n0 = leaf_chain.get_node_by_index(1)    # n0 is the node in leaf chain with index 1
            while n0.get_block_transaction_count(block_index) == 0:
                block_index += 1
                time.sleep(0.2)
            print('-----leaf chain block index is %s-----' % block_index)
            tx_count = n0.get_block_transaction_count(block_index)
            tx_hash = n0.get_transaction_by_block_number_and_index(block_index, tx_index)

            while not tx_hash and tx_index < tx_count:
                tx_index += 1
                print('waiting tx hash')
                time.sleep(0.05)
                tx_hash = n0.get_transaction_by_block_number_and_index(block_index, tx_index)
            pf = n0.get_transaction_proof_by_hash(tx_hash)
            current_chain = leaf_chain
            current_node = n0
            current_pf = pf

            for leaf_node in leaf_chain.nodes:
                leaf_chain.get_log(leaf_node.node_index)
                time.sleep(0.3)
                leaf_chain.search_log(leaf_node.node_index, block_index-1)
                leaf_chain.search_log(leaf_node.node_index, block_index)

        # calculate TPS
        json_files = subprocess.run('ls ../data/*.json', capture_output=True, shell=True)
        files = json_files.stdout.decode(encoding='utf-8').split()

        finish_time = time.time()
        for file in files:
            with open(file, 'rb') as f:
                tx_count = 0
                block_number = "0"
                block_data = json.load(f)
                for k in block_data:
                    if block_data[k]['tx_count'] > 0:
                        block_number = k
                        break
                #         tx_count = block_data[k]['tx_count']
                # if tx_count > 0:
                for i in range(int(block_number)+1, int(block_number)+3):
                    if block_data[str(i)]['tx_count'] > 0:
                        tx_count += block_data[str(i)]['tx_count']
                    else:
                        raise RuntimeError('not enough data')
                time1 = datetime.strptime(block_data[block_number]['written'], '%Y-%m-%d-%H:%M:%S.%f')
                time2 = datetime.strptime(block_data[str(int(block_number)+2)]['written'], '%Y-%m-%d-%H:%M:%S.%f')
                period = (time2 - time1).total_seconds()
                tps = tx_count / period
                with open('../result/single_chain_tps0910.txt', 'a') as tps_file:
                    tps_file.write('%s,%.2f,%s,%d,%s,%.3f,%d\n' % (','.join((map(str, thresh_list[0]))), tps,
                                                                   block_number, tx_count, file,
                                                                   (finish_time-start_time), SEND_TX_SPEED))
        hibe.destruct_hibe_chain()
        time.sleep(10)


