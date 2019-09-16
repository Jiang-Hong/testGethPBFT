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
import json
import subprocess

SEND_TX_SPEED = 120

for _ in range(1):    # iter round
    start_time = time.time()

    ip_list = IPList(ip_file=IP_CONFIG)
    ip_list.stop_all_containers()
    time.sleep(0.5)
    chain_id_list, thresh_list = load_config_file(config_file=CONFIG)
    hibe = HIBEChain(chain_id_list=chain_id_list, thresh_list=thresh_list, ip_list=ip_list)
    hibe.construct_hibe_chain()
    connect_time = time.time()

    hibe.set_number()
    hibe.set_level()
    hibe.set_id()
    end_time = time.time()
    print("connect time %.3fs" % (connect_time - start_time))
    set_up_time = end_time - start_time
    print("total set up time %.3fs" % set_up_time)

    hibe.start_miner()
    time.sleep(2)

    terminal_chains = hibe.structured_chains[-1]
    valid_keys = min([terminal_chain.get_node_by_index(1).key_count() for terminal_chain in terminal_chains])

    threads = []
    for terminal_chain in terminal_chains:
        terminal_node = terminal_chain.get_node_by_index(1)
        t = threading.Thread(target=terminal_node.send_transaction3, args=(valid_keys, 1, 0, 1, SEND_TX_SPEED))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    print('waiting...')
    time.sleep(hibe.max_level * 60)
    print('start')

    # clear data folder
    subprocess.run('rm ../data/*', shell=True)

    leaf_chains = [hibe.get_chain(terminal_chain.get_parent_chain_id()) for terminal_chain in terminal_chains]

    for leaf_chain in leaf_chains:
        block_index = 0
        n0 = leaf_chain.get_node_by_index(1)  # n0 is the node in leaf chain with index 1
        while n0.get_block_transaction_count(block_index) == 0:
            block_index += 1
            time.sleep(0.1)
        for node in leaf_chain.nodes:
            leaf_chain.get_log(node.node_index)
            time.sleep(0.2)
            leaf_chain.search_log(node.node_index, block_index)

            with open('../data/chain%s_node%d.json' % (leaf_chain.chain_id, node.node_index), 'rb') as f:
                block_index_str = str(block_index)
                block_data = json.load(f)
                tx_count = block_data[block_index_str]['tx_count']
                block_index_str = str(block_index+1)
                for k in block_data:
                    if block_data[k]['tx_count'] > tx_count:
                        block_index_str = k
                        tx_count = block_data[k]['tx_count']
                if tx_count > 0:
                    time1 = datetime.strptime(block_data[block_index_str]['written'], '%Y-%m-%d-%H:%M:%S.%f')
                    time2 = datetime.strptime(block_data[str(int(block_index_str) - 1)]['written'],
                                              '%Y-%m-%d-%H:%M:%S.%f')
                    period = (time1 - time2).total_seconds()
                    tps = tx_count / period
                with open('../result/HIBEChain_tps' + str(datetime.utcnow().date()), 'a') as tps_file:
                    tps_file.write('%s,%.2f,%s,%d,%s\n' % (','.join((map(str, thresh_list[0]))), tps, block_index_str,
                                                                tx_count, leaf_chain.chain_id))

