#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import USERNAME, PASSWD
from singlechain import SingleChain
from iplist import IPList
import threading
import time


class HIBEChain():
    """
    Data structure for an Hierarchical Identity Based Encryption Chain.
    """

    def __init__(self, chain_id_list, thresh_list, ip_list, username=USERNAME, password=PASSWD):
        # Check if the input params are legal
        if not len(chain_id_list) == len(thresh_list):
            raise ValueError("length of chain_id_list should match length of thresh_list")
        needed_count = sum(node_count for (node_count, _) in thresh_list)
        containers_count = ip_list.get_full_count()
        if needed_count > containers_count:
            raise ValueError("%d containers needed but only %d containers available" % (needed_count, containers_count))

        self.username = username
        self.password = password
        self.chains = []
        self.chain_id_list = chain_id_list
        self.thresh_list = thresh_list
        self.ip_list = ip_list
        self.max_level = len(chain_id_list[-1]) // 4
        self.if_set_number = False
        self.if_set_level = False
        self.if_set_id = False
        self.structed_chains = []

        self.init_chains()

        threads = []
        for level in self.structed_chains[:-1]:
            for chain in level:
                t = threading.Thread(target=chain.config_consensus_chain, args=())
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        threads = []
        if not self.structed_chains[-1][0].is_terminal:
            for chain in self.structed_chains[-1]:
                t = threading.Thread(target=chain.config_consensus_chain, args=())
                t.start()
                threads.append(t)
        else:
            for chain in self.structed_chains[-2]:
                chain.config_leaf_chain(self.structed_chains[-1])
            for chain in self.structed_chains[-1]:
                t = threading.Thread(target=chain.config_terminal, args=())
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        time.sleep(1)

        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.run_nodes, args=())
            t.start()
            threads.append(t)
            # time.sleep(1)
        for t in threads:
            t.join()
        time.sleep(3)

    def construct_hibe_chain(self):
        """
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with their parent blockchain nodes.
        """
        print('construct hibe chain')
        threads = []
        for chain in self.chains[::-1]:
            if chain.get_chain_id() != '':
                parent_chain = self.chains[self.chain_id_list.index(chain.get_chain_id()[:-4])]
                #                parent_chain.connect_lower_chain(chain)
                t = threading.Thread(target=parent_chain.connect_lower_chain, args=(chain,))
                t.start()
                threads.append(t)
                # time.sleep(1)
        print('active threads:', threading.active_count())
        for t in threads:
            t.join()
        time.sleep(2)

    def destruct_hibe_chain(self):
        """Stop all containers to destruct the HIBEChain."""
        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.destruct_chain, args=())
            t.start()
            threads.append(t)
            time.sleep(0.1)
        for t in threads:
            t.join()

    def get_chain(self, ID):
        """Return a list of blockchain nodes with a given chain ID(eg. '00010001')."""
        try:
            index = self.chain_id_list.index(ID)
            return self.chains[index]
        except ValueError or IndexError:
            print("ID %s is not in the HIBEChain" % ID)

    def get_parent_chain(self, chain):
        """
        Return parent chain.
        Return None if current chain is root chain.
        """
        if chain.chain_id == '':
            print('root chain does not have a parent chain')
            return None
        else:
            parent_chain_id = chain.chain_id[:-4]
            return self.get_chain(parent_chain_id)

    def is_root_chain(self, chain):
        """Check if chain is root chain."""
        return chain.chain_id == ''

    def init_chains(self):
        threads = []
        # count = 0
        level = 0
        tmp_chain = list()
        for index, name in enumerate(self.chain_id_list):
            if name:
                print("name is %s" % name, end=" ")
            else:
                print("name is blank", end=" ")
            current_level = len(name) // 4
            node_count, threshold = self.thresh_list[index][0], self.thresh_list[index][1]
            blockchain_id = 120 + index
            tmp = SingleChain(name, current_level, node_count, threshold, blockchain_id, self.ip_list, self.username,
                              self.password)
            self.chains.append(tmp)
            if current_level == level:
                tmp_chain.append(tmp)
            else:
                self.structed_chains.append(tmp_chain)
                tmp_chain = list()
                tmp_chain.append(tmp)
                level = current_level
            t = threading.Thread(target=tmp.singlechain_start)
            t.start()
            threads.append(t)
            time.sleep(0.1)
        self.structed_chains.append(tmp_chain)

        print()

        for t in threads:
            t.join()
        for ch in self.structed_chains[-1]:
            if ch.threshold == 1:
                ch.is_terminal = True

    def set_number(self):
        """Set (n, t) value for all chains in HIBEChain."""
        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.set_number, args=())
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.if_set_number = True
        time.sleep(1)

    def set_level(self):
        """Set level value for all chains in HIBEChain."""

        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.set_level, args=(self.max_level,))
            t.start()
            threads.append(t)
        print('waiting for set level')
        for t in threads:
            print('.', end='')
            t.join()
        self.if_set_level = True
        time.sleep(1)

    def set_id(self):
        """Set ID for all chains in HIBEChain."""

        if not self.if_set_number and self.if_set_level:
            raise RuntimeError("number and level info should be set previously")
        start_time = time.time()
        threads = []
        for index, level in enumerate(self.structed_chains):
            for chain in level:
                t = threading.Thread(target=chain.set_id)
                t.start()
                threads.append(t)
                time.sleep(0.1)
            for t in threads:
                t.join()

            print('waiting for delivering key')
            if index == 0:
                sleep_time = max([chain.node_count for chain in level]) * 10
                print('root level waiting...%ds' % sleep_time)
                time.sleep(sleep_time)
                while not all([node.key_status() for node in chain.nodes for chain in level]):
                    print('root level waiting...')
                    time.sleep(5)
                time.sleep(5)
            else:
                #                thresh = max((chain.threshold for chain in level))
                while not all([node.key_status() for node in chain.nodes for chain in level]):
                    print('.', end='')
                    time.sleep(2)
                time.sleep(2)
        self.if_set_id = True
        print("------setID finished----------------")
        end_time = time.time()
        print('setID elapsed time %.2f' % (end_time - start_time))

    def start_miner(self):
        """Start miner for all consensus nodes."""

        for level in self.structed_chains[:-1]:
            for chain in level:
                chain.start_miner()


if __name__ == "__main__":
    ip_list = IPList('ip.txt')
    chain_id_list = ["", "0001", "0002"]
    thresh_list = [(4, 3), (1, 1), (1, 1)]

    hibe = HIBEChain(chain_id_list, thresh_list, ip_list)
    hibe.construct_hibe_chain()

    hibe.set_number()
    hibe.set_level()
    hibe.set_id()
    time.sleep(1)

    a = hibe.get_chain("")
    a1 = a.get_node_by_index(1)
    print("level 0 keystatus", a1.key_status())
    b = hibe.get_chain("0001")
    b1 = b.get_node_by_index(1)
    print("level 1 keystatus", b1.key_status())

    hibe.destruct_hibe_chain()
