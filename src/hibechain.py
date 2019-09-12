#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from const import USERNAME, PASSWD, IP_CONFIG, CONFIG
from conf import load_config_file
from singlechain import SingleChain
from iplist import IPList
import threading
import time


class HIBEChain(object):
    """
    Data structure for an Hierarchical Identity Based Encryption Chain.
    """

    def __init__(self, chain_id_list: [str], thresh_list: [tuple], ip_list: IPList,
                 username: str = USERNAME, password: str = PASSWD) -> None:
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
        self.structured_chains = []
        self.chain_id_list = chain_id_list
        self.thresh_list = thresh_list
        self.ip_list = ip_list
        self.max_level = len(chain_id_list[-1]) // 2
        self.if_set_number = False
        self.if_set_level = False
        self.if_set_id = False

        self.init_chains()

        threads = []
        for level in self.structured_chains[:-1]:
            for chain in level:
                t = threading.Thread(target=chain.config_consensus_chain)
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        threads = []
        if not self.structured_chains[-1][0].is_terminal:    # no terminals
            for chain in self.structured_chains[-1]:
                t = threading.Thread(target=chain.config_consensus_chain)
                t.start()
                threads.append(t)
        else:    # terminals
            for chain in self.structured_chains[-2]:
                print('--------------')
                print('config leaf chains-----------------------')
                chain.config_leaf_chain(self.structured_chains[-1])    # config leaf chains
                # break  # TODO need to be optimized
            for chain in self.structured_chains[-1]:
                print('-----------------')
                print('----------------------config terminals')
                t = threading.Thread(target=chain.config_terminal)    # config terminals
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

        time.sleep(3)

        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.run_nodes)
            t.start()
            threads.append(t)
            # time.sleep(1)
        for t in threads:
            t.join()
        time.sleep(0.5)

    def construct_hibe_chain(self) -> None:
        """
        Construct the hierarchical construction of the HIBEChain.
        Connect blockchain nodes with their parent blockchain nodes.
        """
        time.sleep(1)
        print('construct hibe chain')
        threads = []
        for chain in self.chains[::-1]:
            if chain.chain_id != '':
                parent_chain = self.chains[self.chain_id_list.index(chain.chain_id[:-2])]
                #                parent_chain.connect_lower_chain(chain)
                t = threading.Thread(target=parent_chain.connect_lower_chain, args=(chain,))
                t.start()
                threads.append(t)
                time.sleep(1)
        # print('active threads:', threading.active_count())
        for t in threads:
            t.join()
        time.sleep(1)
        # TODO check peer count

    def __repr__(self) -> str:
        return ' '.join([str(chain.chain_id) for chain in self.chains])

    def __str__(self) -> str:
        return '\n'.join([chain.__str__() for chain in self.chains])

    def is_connected(self) -> bool:
        for level in self.structured_chains:
            for chain in level:
                parent = self.get_parent_chain(chain)
                children = self.get_child_chains(chain)
                peer_count = chain.node_count - 1
                if parent:
                    peer_count += parent.node_count
                if children:
                    for child in children:
                        peer_count += child.node_count
                for node in chain.nodes:
                    tmp_count = node.get_peer_count()
                    if tmp_count != peer_count:
                        print('%s %s peer count is %d, should be %d' % (chain, node, tmp_count, peer_count))
                        return False
        return True

    def destruct_hibe_chain(self) -> None:
        """Stop all containers to destruct the HIBEChain."""
        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.destruct_chain)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def get_chain(self, chain_id: str = '') -> SingleChain:
        """Return a list of blockchain nodes with a given chain ID(eg. '00010001')."""
        try:
            index = self.chain_id_list.index(chain_id)
            return self.chains[index]
        except ValueError or IndexError:
            print("ID %s is not in the HIBEChain" % chain_id)

    def get_parent_chain(self, chain: SingleChain) -> Optional[SingleChain]:
        """
        Return parent chain.
        Return None if current chain is root chain.
        """
        if chain.chain_id == '':
            print('root chain does not have a parent chain')
            return None
        else:
            parent_chain_id = chain.chain_id[:-2]
            return self.get_chain(parent_chain_id)

    def get_child_chains(self, chain: SingleChain) -> [SingleChain]:
        """
        Return a list of child chains.
        Return empty list if no child chain.
        """
        child_chains = []
        for level in self.structured_chains[1:]:
            if level[0].chain_id[:-2] == chain.chain_id:
                child_chains.extend(level)
        return child_chains

    def init_chains(self) -> None:
        threads = []
        # count = 0
        level = 0
        tmp_chain = list()
        for index, name in enumerate(self.chain_id_list):
            if name:
                print("name is %s" % name, end=" ")
            else:
                print("name is blank", end=" ")
            current_level = len(name) // 2
            node_count, threshold = self.thresh_list[index][0], self.thresh_list[index][1]
            blockchain_id = 120 + index
            tmp = SingleChain(name, current_level, node_count, threshold, blockchain_id, self.ip_list, self.username,
                              self.password)
            self.chains.append(tmp)
            if current_level == level:
                tmp_chain.append(tmp)
            else:
                self.structured_chains.append(tmp_chain)
                tmp_chain = list()
                tmp_chain.append(tmp)
                level = current_level
            t = threading.Thread(target=tmp.singlechain_start)
            t.start()
            threads.append(t)
            # time.sleep(0.1)   ####
        self.structured_chains.append(tmp_chain)

        print()

        for t in threads:
            t.join()
        for ch in self.structured_chains[-1]:
            if ch.threshold == 1:
                ch.is_terminal = True

    def set_number(self) -> None:
        """Set (n, t) value for all chains in HIBEChain."""
        threads = []
        for chain in self.chains:
            t = threading.Thread(target=chain.set_number, args=())
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.if_set_number = True
        time.sleep(0.3)

    def set_level(self) -> None:
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
        time.sleep(0.3)

    def set_id(self) -> None:
        """Set ID for all chains in HIBEChain."""

        if not self.if_set_number and self.if_set_level:
            raise RuntimeError("number and level info should be set previously")
        start_time = time.time()
        threads = []
        for index, level in enumerate(self.structured_chains):
            # variable level means all chains in the same level
            for chain in level:
                t = threading.Thread(target=chain.set_id)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

            print('waiting for delivering key')
            if index == 0:
                time.sleep(max([chain.node_count for chain in level])*5)  # *5
                # sleep_time = max([chain.node_count for chain in level]) * 10
                # print('root level waiting...%ds' % sleep_time)
                # time.sleep(sleep_time)
                while not all([node.key_status() for chain in level for node in chain.nodes]):
                    print('root level waiting ')
                    time.sleep(5)
            else:
                threads = []
                for chain in level:
                    t = threading.Thread(target=self.gen_key, args=(chain, ))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()

                # for chain1 in level:
                #     true_count = 0
                #     if chain1.is_terminal:  # setting terminal node keys
                #         print('setting terminal keys')
                #         terminal_node = chain1.get_node_by_index(1)
                #
                #         while True:
                #             result = terminal_node.key_status()
                #             if result is False:
                #                 time.sleep(2)
                #                 terminal_node.set_id(chain1.chain_id)
                #                 time.sleep(3)
                #             else:
                #                 break
                #         print('40s waiting for key generation...')
                #         time.sleep(40)
                #         key_count = terminal_node.key_count()
                #         while True:
                #             print('another 10s waiting for key generation...')
                #             time.sleep(10)
                #             tmp_count = terminal_node.key_count()
                #             if tmp_count != 0 and tmp_count == key_count:
                #                 break
                #             # if tmp_count == 0:
                #             #     chain1.set_id()
                #             key_count = tmp_count
                #
                #         print('terminal keys generated.')
                #
                #     else:
                #         while True:
                #             for node in chain1.nodes:
                #                 print('%s:%s waiting for key' % (node.ip.address, node.rpc_port))
                #                 result = node.key_status()
                #                 if result is True:
                #                     true_count += 1
                #                 else:
                #                     node.set_id(chain1.chain_id)
                #             print('true count is:', true_count)
                #             if true_count >= chain1.threshold:
                #                 break
                #             else:
                #                 time.sleep(5)
                #
                # # while not all([node.key_status() for node in chain.nodes for chain in level]):
                # #     print('level %d is not ready, waiting...' % index)
                # #     time.sleep(5)
                time.sleep(2)
        self.if_set_id = True
        print("------setID finished----------------")
        end_time = time.time()
        print('setID elapsed time %.2f' % (end_time - start_time))

    def start_miner(self) -> None:
        """Start miner for all consensus nodes."""

        for level in self.structured_chains[:-1]:
            for chain in level:
                chain.start_miner()

    @staticmethod
    def gen_key(single_chain: SingleChain) -> None:
        if single_chain.is_terminal:  # setting terminal node keys
            print('setting terminal keys for chain', single_chain.chain_id)
            terminal_node = single_chain.get_node_by_index(1)
            while True:
                result = terminal_node.key_status()
                if result is False:
                    time.sleep(2)
                    terminal_node.set_id(single_chain.chain_id)
                    time.sleep(3)
                else:
                    break
            print('40s waiting for key generation...')
            time.sleep(40)
            key_count = terminal_node.key_count()
            while True:
                print('another 10s waiting for key generation...')
                time.sleep(10)
                tmp_count = terminal_node.key_count()
                if tmp_count != 0 and tmp_count == key_count:
                    break
                # if tmp_count == 0:
                #     chain1.set_id()
                key_count = tmp_count

            print(key_count, 'terminal keys generated.')

        else:
            true_count = 0
            while True:
                for node in single_chain.nodes:
                    print('%s:%s waiting for key' % (node.ip.address, node.rpc_port))
                    result = node.key_status()
                    if result is True:
                        true_count += 1
                    else:
                        node.set_id(single_chain.chain_id)
                print('true count is:', true_count)
                if true_count >= single_chain.threshold:
                    break
                else:
                    time.sleep(5)


if __name__ == "__main__":
    ip_list = IPList(IP_CONFIG)
    ip_list.stop_all_containers()
    chain_id_list, thresh_list = load_config_file(CONFIG)
    # chain_id_list = ["", "01", "02"]
    # thresh_list = [(4, 3), (1, 1), (1, 1)]

    hibe = HIBEChain(chain_id_list, thresh_list, ip_list)
    hibe.construct_hibe_chain()

    hibe.set_number()
    hibe.set_level()
    hibe.set_id()

    # hibe.destruct_hibe_chain()