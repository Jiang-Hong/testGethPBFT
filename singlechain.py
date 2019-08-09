#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import IP_CONFIG, USERNAME, PASSWD
from gethnode import GethNode
from iplist import IPList
from conf import generate_genesis, generate_leaf_genesis
from typing import Any
import time
from datetime import datetime
import subprocess
import threading
import json
from collections import defaultdict
import os

# class SetGenesis():
#     """Decorator. Set genesis.json file for a chain."""
#     def __init__(self, func):
#         self.func = func
#     def __call__(self, *args):
#         pass
#     def __repr__(self):
#         """Return the function's docstring."""
#         return self.func.__doc__
#     def __get__(self, obj, objtype):
#         """Support instance methods."""
#         return functools.partial(self.__call__, obj)


# def add_peer(node1: GethNode, node2: GethNode, label: int):
#     # Use semaphore to limit number of concurrent threads
#     SEMAPHORE.acquire()
#     node1.add_peer(node2.enode, label)
#     # time.sleep(0.5)
#     SEMAPHORE.release()
#     # print(threading.active_count())


class SingleChain(object):
    """
    Data structure for a set of Geth-pbft clients for a single blockchain.
    """

    def __init__(self, name: str, level: int, node_count: int, threshold: int,
                 blockchain_id: int, ip_list: IPList, username: str = USERNAME, password: str = PASSWD) -> None:
        # Check if the input params are legal.
        if node_count > ip_list.get_full_count():
            raise ValueError("not enough IPs")
        self.username = username
        self.password = password
        self._level = level
        self._chain_id = name    # chain id
        self.node_count = node_count
        self.threshold = threshold
        self.blockchain_id = blockchain_id
        self.ip_list = ip_list
        self._nodes = []
        self._ips = set()
        self.if_set_number = False
        self.if_set_level = False
        self.if_set_id = False
        self.is_terminal = False
        self.config_file = None
        self.accounts = []
        self.all_ip_port = set() # set of (ip_address, port)
        self.map = {} # map of (ip_address, port) to node

    def singlechain_start(self) -> None:
        """Start all containers for a single chain."""
        threads = []
        for index in range(self.node_count):
            pbft_id = index
            node_index = index + 1
            tmp = GethNode(self.ip_list, pbft_id, node_index, self.blockchain_id, self.username, self.password)
            ip_port = (tmp.ip.address, tmp.ethereum_network_port)
            self.all_ip_port.add(ip_port)
            self.map.setdefault(ip_port, tmp)
            self.ips.add(tmp.ip)
            self.nodes.append(tmp)
            # xq start a thread， target stand for a function that you want to run ,args stand for the parameters
            t = threading.Thread(target=tmp.start)
            t.start()
            threads.append(t)
            time.sleep(0.4)

        for t in threads:
            # xq threads must run the join function, because the resources of main thread is needed
            t.join()

        time.sleep(0.1)
        for index in range(self.node_count):
            self.accounts.append(self.nodes[index].accounts[0])
#        print(self.accounts)

    def __str__(self) -> str:
        return ', '.join([chain_node.__repr__() for chain_node in self._nodes])

    def __repr__(self) -> str:
        return self.chain_id if self.chain_id else 'root chain'

    @property
    def nodes(self) -> [GethNode]:
        """Return nodes in the chain"""
        return self._nodes

    @property
    def ips(self) -> set:
        """Return a set of IP objects in the chain"""
        return self._ips

    @property
    def level(self) -> int:
        """Return level of the chain in HIBE chain."""
        return self._level

    @property
    def chain_id(self) -> str:
        """return chain id of the chain."""
        return self._chain_id

    def config_genesis(self) -> None:
        """Copy genesis.json file into a container."""
        for server_ip in self.ips:
            subprocess.run(['sshpass -p %s scp config/%s %s@%s:%s' % (self.password, self.config_file,
                           self.username, server_ip.address, self.config_file)], stdout=subprocess.PIPE, shell=True)
            time.sleep(self.node_count/50)
            threads = []
            for node in self.nodes:
                if node.ip == server_ip:
                    command = 'docker cp %s %s:/root/%s' % (self.config_file, node.name, self.config_file)
                    t = threading.Thread(target=server_ip.exec_command, args=(command,))
                    t.start()
                    threads.append(t)
                    print('copying genesis file')
                    time.sleep(0.1)
            for t in threads:
                t.join()
        time.sleep(1)

    def config_consensus_chain(self) -> None:
        """Set genesis.json for a blockchain & init with genesis.json."""
        if self.chain_id is "":
            self.config_file = '0.json'
        else:
            self.config_file = '%s.json' % self.chain_id
        generate_genesis(self.blockchain_id, self.accounts, self.config_file)
        time.sleep(0.02)
        self.config_genesis()

    def config_leaf_chain(self, leaf_chains: ['SingleChain']) -> None:
        """Set genesis.json for leaf chains."""
        if self.chain_id is "":
            self.config_file = '0.json'
        else:
            self.config_file = '%s.json' % self.chain_id
        generate_leaf_genesis(self.config_file, leaf_chains)
        time.sleep(0.02)
        self.config_genesis()

    def config_terminal(self) -> None:
        """Set genesis.json for terminal equipments."""
        if len(self.chain_id) == 2:
            self.config_file = '0.json'
        else:
            self.config_file = '%s.json' % self.chain_id[:-2]
        self.config_genesis()

    def run_nodes(self) -> None:
        """Run nodes on a chain."""
        self.init_geth()
        self.run_geth_nodes()
        time.sleep(1)
        self.construct_chain()

    def init_geth(self) -> None:
        """
        run geth init command for nodes in a chain
        """
        if self.config_file is None:
            raise ValueError("initID is not set")
        threads = []
        for server_ip in self.ips:
            for node in self.nodes:
                if node.ip == server_ip:
                    init_geth_command = 'docker exec -t %s geth --datadir abc init %s' % (node.name, self.config_file)
                    t = threading.Thread(target=server_ip.exec_command, args=(init_geth_command,))
                    t.start()
                    threads.append(t)
        time.sleep(0.3)
        for t in threads:
            t.join()

    def run_geth_nodes(self):
        threads = []
        for node in self.nodes:
            # Making the personal API available over RPC is not safe. Use IPC instead of RPC is safer.
            start_geth_command = ('/usr/bin/geth --datadir abc --cache 1024 --port 30303 --rpcport 8545 --rpcapi '
                                  'admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr 0.0.0.0 '
                                  '--pbftid %d --nodeindex %d --blockchainid %d --unlock %s --password '
                                  'passfile --maxpeers 1024 --maxpendpeers 1024 --txpool.globalslots 81920 '
                                  '--txpool.globalqueue 81920 --syncmode full '
                                  '--nodiscover >> %s.log 2>&1') % (node.pbft_id, node.node_index,
                                                     node.blockchain_id, node.accounts[0], node.name)
            # start_geth_command = ('/usr/bin/geth --datadir abc --cache 1024 --port 30303 --rpcport 8545 --rpcapi '
            #                       'admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr 0.0.0.0 '
            #                       '--pbftid %d --nodeindex %d --blockchainid %d --unlock %s --password '
            #                       'passfile --maxpeers 1024 --maxpendpeers 1024 --txpool.globalslots 81920 '
            #                       '--txpool.globalqueue 81920 --syncmode full '
            #                       '--nodiscover') % (node.pbft_id, node.node_index,
            #                                                         node.blockchain_id, node.accounts[0])
            command = 'docker exec -td %s bash -c  \"%s\" ' % (node.name, start_geth_command)
            print(start_geth_command)
            t = threading.Thread(target=node.ip.exec_command, args=(command,))
            t.start()
            threads.append(t)
        time.sleep(0.8)
        for t in threads:
            t.join()
        print('node starting')
        # must wait here
        for _ in range(4):
            print('.', end='')
            time.sleep(1)
        print()

        threads = []
        for node in self.nodes:
            t = threading.Thread(target=node.set_enode)
            t.start()
            threads.append(t)
            time.sleep(0.05)
        for t in threads:
            t.join()
        time.sleep(2)

    def is_root_chain(self):
        """Check if chain is root chain."""
        return self.chain_id == ""

    def get_primer_node(self) -> GethNode:
        """Return the primer node of the set of Geth-pbft clients."""
        return self.nodes[0]

    def get_node_by_index(self, node_index: int) -> GethNode:
        """Return the node of a given index."""
        if node_index <= 0 or node_index > len(self.nodes):
            raise ValueError("node index out of range")
        return self.nodes[node_index-1]

    def construct_chain(self) -> None:
        """Construct a single chain."""
        if not self.is_terminal:
            print("constructing single chain")
            start_time = time.time()
            threads = []

            # connect nodes in a single chain with each other
            for i in range(self.node_count):
                for j in range(i+1, self.node_count):
                    # self.nodes[i].add_peer(self.nodes[j].enode, 0)
                    t = threading.Thread(target=self.nodes[i].add_peer, args=(self.nodes[j].enode, 0))
                    t.start()
                    threads.append(t)
                    time.sleep(0.05)
                    t1 = threading.Thread(target=self.nodes[j].add_peer, args=(self.nodes[i].enode, 0))
                    # time.sleep(0.02)  # necessary
                    t1.start()
                    threads.append(t1)
                    time.sleep(0.05)
                break    # in case of too many addPeer requests
            for t in threads:
                t.join()
            # print('active threads:', threading.active_count())

            print("-----------chain construction waiting--------------")
            time.sleep(self.node_count//4 + 2)  #

            for index, node in enumerate(self.nodes):
                while node.get_peer_count() != self.node_count - 1:
                    # node_peers_info = node.get_peers()
                    # peers = {tuple(item['network']['remoteAddress'].split(':')) for item in node_peers_info}
                    # node_peers = {(ip_address, int(port)) for ip_address, port in peers}
                    # node_peers.add((node.ip.address, node.ethereum_network_port))
                    # print('node peers', node_peers)
                    # un_connected_peers = self.all_ip_port.difference(node_peers)
                    # print('~~~~~~~~~~~~~~')
                    # print('all', self.all_ip_port)
                    # print('unconnected', un_connected_peers)
                    # print('~~~~~~~~~~~~~~')
                    # print('unconnected peers: %d' % len(un_connected_peers))
                    # print('------------------')
                    # print(index, un_connected_peers)
                    # print('------------------')
                    # for ip_port in un_connected_peers:
                    #     peer2connect = self.map[ip_port]
                    #     node.add_peer(peer2connect.enode, 0)
                    #     time.sleep(0.3)
                    #     peer2connect.add_peer(node.enode, 0)
                    #     time.sleep(0.2)
                    # time.sleep(len(un_connected_peers) // 4 + 2)
                    print('not enough peers', index)
                    threads = []
                    for m in range(index, self.node_count):
                        for n in range(m+1, self.node_count):
                            t = threading.Thread(target=self.nodes[n].add_peer, args=(self.nodes[m].enode, 0))
                            time.sleep(0.01)
                            t.start()
                            threads.append(t)
                        break  ###
                    for t in threads:
                        t.join()
                        # node.add_peer(other_node.enode, 0)
                    time.sleep(0.5)
                    if node.get_peer_count() != self.node_count - 1:
                        print('waiting for peers')
                        time.sleep(self.node_count-index)
                        # break #TODO delete this line?
                    else:
                        time.sleep(0.5)
                        break

            end_time = time.time()
            print('construction complete: %.3fs' % (end_time - start_time))

            # while not all([node.get_peer_count() == self.node_count-1 for node in self.nodes]):
            #     iter_count += 1
            #     print('waiting time: %f, waiting round is %d' % (0.5 * iter_count, iter_count))
            #     if iter_count == 10:
            #         for node in self.nodes[1:]:
            #             if node.get_peer_count() != self.nodes[0].get_peer_count():
            #                 print('add peer again')
            #                 node.add_peer(self.nodes[0].enode, 0)
            #         iter_count = 0

    # def construct_chain(self) -> None:
    #     """Use static-nodes.json to construct single chain."""
    #     if not self.is_terminal:
    #         print('constructing single chain...')
    #         enodes = []
    #         for node in self.nodes:
    #             enodes.append(node.enode)
    #         pass

    def get_parent_chain_id(self) -> str:
        """Return chain ID of parent chain."""
        if self.chain_id == '':
            print("Root chain has no parent chain.")
            return ''
        else:
            return self.chain_id[:-2]

    def destruct_chain(self) -> None:
        """Stop containers to destruct the chain."""
        threads = []
        for node in self.nodes:
            t = threading.Thread(target=node.stop)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def connect_lower_chain(self, other_chain: 'SingleChain') -> None:
        """Connect to a lower level single chain."""
        time.sleep(0.01)
        threads = []
        for node in self.nodes:
            for other in other_chain.nodes:
                t = threading.Thread(target=other.add_peer, args=(node.enode, 2))    # param 2 means upper peer
                t.start()
                time.sleep(0.05)    # if fail. increase this value.
                threads.append(t)
                t1 = threading.Thread(target=node.add_peer, args=(other.enode, 1))  # param 1 means lower peer
                t1.start()
                time.sleep(0.05)
                threads.append(t1)
                # time.sleep(0.3)
            break

        for t in threads:
            t.join()
        time.sleep(self.node_count//5+1)

    def connect_upper_chain(self, other_chain: 'SingleChain') -> None:
        """Connect to an upper level single chain."""
        time.sleep(0.05)
        threads = []
        for node in self.nodes:
            for other in other_chain.nodes:
                ep = other.enode
                t = threading.Thread(target=node.add_peer, args=(ep, 2))    # param 2 means upper peer
                t.start()
                threads.append(t)
                time.sleep(0.05)
        for t in threads:
            t.join()
        time.sleep(self.node_count//5+1)

    def get_node_count(self) -> int:
        """Return the number of nodes of the blockchain."""
        return len(self.nodes)

    def set_number(self) -> None:
        """Set (number, threshold) value for the nodes of the blockchain."""
        if not self.if_set_number:
            p = self.get_primer_node()
            p.set_number(self.node_count, self.threshold)
            self.if_set_number = True
        else:
            raise RuntimeError("number of chain %s already set" % self.chain_id)
        time.sleep(0.5*(len(self.nodes)//10+1))

    def set_level(self, max_level: int) -> None:
        """Set level info for each node."""
        threads = []
        if not self.if_set_level:
            for node in self.nodes:
                t = threading.Thread(target=node.set_level, args=(self.level, max_level))
                t.start()
                threads.append(t)
                time.sleep(0.02)
            for t in threads:
                t.join()
            self.if_set_level = True
            time.sleep(0.05)
        else:
            raise RuntimeError("level of chain %s already set" % self.chain_id)

    def set_id(self) -> None:
        """Set ID for a blockchain."""
        if not self.if_set_number and self.if_set_level:
            raise RuntimeError("number and level info should be set previously")
        if len(self.chain_id) // 2 != self.level:
            raise ValueError("length of id should match level number")
        time.sleep(0.05)
        if not self.if_set_id:
            if self.level == 0:
                p = self.get_primer_node()
                p.set_id("")
            else:
                threads = []
                for node in self.nodes:
                    t = threading.Thread(target=node.set_id, args=(self.chain_id,))
                    t.start()
                    threads.append(t)
                    time.sleep(0.3)
                for t in threads:
                    t.join()
            self.if_set_id = True
        else:
            raise RuntimeError("ID of chain %s already set" % self.chain_id)

    def start_miner(self) -> None:
        """Start miners of all nodes on the chain."""
        if not self.is_terminal:
            threads = []
            for node in self.nodes:
                t = threading.Thread(target=node.start_miner)
                t.start()
                threads.append(t)
                time.sleep(0.02)
            for t in threads:
                t.join()

    def get_log(self, node_index: int) -> None:
        time.sleep(2)
        node = self.get_node_by_index(node_index)
        filename = 'chain%s_node%d.txt' % (self.chain_id, node_index)
        # check if the log file exists, if True, do nothing
        if os.path.exists('data/%s' % filename):
            print('log exists')
        else:
            node.ip.exec_command('docker cp %s:/root/result%d ./%s' % (node.name, node_index, filename))
            time.sleep(0.3)
            copy_command = 'sshpass -p %s scp %s@%s:%s ./data/' % (self.password, self.username, node.ip.address, filename)
            subprocess.run(copy_command, stdout=subprocess.PIPE, shell=True)

    def search_log(self, node_index: int, block_index: int, if_get_block_tx_count: bool = True) -> None:
        node = self.get_node_by_index(node_index)
        filename = 'data/chain%s_node%d.txt' % (self.chain_id, node_index)
        # map of (block index, {block prepare time: t1, block consensus confirm time: t2, block written time: t3})
        block_time = defaultdict(dict)
        with open(filename, 'r') as log:
            for line in log.readlines():
                line = line.strip()
                arr = line.split()
                if arr[0].startswith('block'):
                    tmp = arr[-4].split('.')
                    tmp[1] = tmp[1][:6]
                    arr[-4] = '.'.join(tmp)
                    arr[-5] = arr[-5][1:]
                    arr[-5] += '-' + arr[-4]
                    block_time[arr[1]][arr[2]] = arr[-5]
        # print(block_time)
        if if_get_block_tx_count:
            for index_str in block_time.keys():
                index = int(index_str)
                tx_count = node.get_block_transaction_count(index)
                block_time[index_str]['tx_count'] = tx_count

        json_name = 'data/chain%s_node%d.json' % (self.chain_id, node_index)
        json_str = json.dumps(block_time, indent=2)
        with open(json_name, 'w') as f:
            print(json_str, file=f)

        written_time_str = block_time[str(block_index)]['written']
        written_time = datetime.strptime(written_time_str, '%Y-%m-%d-%H:%M:%S.%f')    # type: datetime
        tx_count = block_time[str(block_index)]['tx_count']
        with open('data/elapsed_time.txt', 'a') as log:
            log.write('%s block index: %d, time: %s  TX count:%d\n' % (filename, block_index, written_time, tx_count))


if __name__ == "__main__":
    ip_list = IPList(IP_CONFIG)
    ip_list.stop_all_containers()
    node_count = 4
    c = SingleChain('01', 1, node_count, node_count*2//3+1, 121, ip_list)
    c.singlechain_start()
    c.config_consensus_chain()
    c.run_nodes()
#    p = c.get_primer_node()
#    print(p.get_peer_count())

    time.sleep(node_count//3)
    fail_count = 0
    for i in range(1, node_count + 1):
        node = c.get_node_by_index(i)
        #        acc = node.getAccounts()[0]
        #        print(acc)
        #        print(node.getBalance(acc))
        count = node.get_peer_count()
        print(count)
        if count != node_count - 1:
            fail_count += 1
    print("fail count:", fail_count)
    # c.destruct_chain()
