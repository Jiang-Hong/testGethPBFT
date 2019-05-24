#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from const import IP_CONFIG, USERNAME, PASSWD
from gethnode import GethNode
from iplist import IPList
from conf import generate_genesis, generate_leaf_genesis
from functools import wraps
import time
import subprocess
import threading


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
#     node1.add_peer(node2.get_enode(), label)
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
        self.level = level
        self.chain_id = name    # chain id
        self.node_count = node_count
        self.threshold = threshold
        self.blockchain_id = blockchain_id
        self.ip_list = ip_list
        self.nodes = []
        self.ips = set()
        self.if_set_number = False
        self.if_set_level = False
        self.if_set_id = False
        self.is_terminal = False
        self.config_file = None
        self.accounts = []

    def singlechain_start(self) -> None:
        """Start all containers for a single chain."""
        threads = []
        for index in range(self.node_count):
            pbft_id = index
            node_index = index + 1
            tmp = GethNode(self.ip_list, pbft_id, node_index, self.blockchain_id, self.username, self.password)
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

        for index in range(self.node_count):
            self.accounts.append(self.get_nodes[index].accounts[0])
#        print(self.accounts)

    def __repr__(self) -> str:
        return self.chain_id if self.chain_id else 'root chain'

    @property
    def get_nodes(self) -> [GethNode]:
        """Return nodes in the chain"""
        return self.nodes

    @property
    def get_ips(self) -> set:
        """Return a set of IP objects in the chain"""
        return self.ips

    @property
    def get_level(self) -> int:
        """Return level of the chain in HIBE chain."""
        return self.level

    def config_genesis(self) -> None:
        """Copy genesis.json file into a container."""
        for server_ip in self.get_ips:
            subprocess.run(['sshpass -p %s scp docker/%s %s@%s:%s' % (self.password, self.config_file,
                           self.username, server_ip.address, self.config_file)], stdout=subprocess.PIPE, shell=True)
            time.sleep(self.node_count/50)
            threads = []
            for node in self.get_nodes:
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
            start_geth_command = ('geth --datadir abc --cache 512 --port 30303 --rpcport 8545 --rpcapi '
                                  'admin,eth,miner,web3,net,personal,txpool --rpc --rpcaddr \"0.0.0.0\" '
                                  '--pbftid %d --nodeindex %d --blockchainid %d --unlock %s --password '
                                  '\"passfile\" --maxpeers 1024 --maxpendpeers 1024 --txpool.globalslots 81920 '
                                  '--txpool.globalqueue 81920 --syncmode \"full\" '
                                  '--nodiscover') % (node.pbft_id, node.node_index,
                                                     node.blockchain_id, node.accounts[0])
            command = 'docker exec -td %s %s' % (node.name, start_geth_command)
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

    def get_chain_id(self) -> str:
        """return chain id of the chain."""
        return self.chain_id

    def is_root_chain(self):
        """Check if chain is root chain."""
        return self.chain_id == ""

    def get_primer_node(self) -> GethNode:
        """Return the primer node of the set of Geth-pbft clients."""
        return self.nodes[0]

    def get_node_by_index(self, node_index:int) -> GethNode:
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
            node_count = len(self.nodes)

            # connect nodes in a single chain with each other
            for i in range(node_count):
                for j in range(i+1, node_count):
                    t1 = threading.Thread(target=self.nodes[i].add_peer, args=(self.nodes[j].get_enode(), 0))
                    t1.start()
                    time.sleep(0.1)    # necessary
                    threads.append(t1)
                break
            for t in threads:
                t.join()
            # print('active threads:', threading.active_count())
            end_time = time.time()
            print('%.3fs' % (end_time - start_time))
            print("-------------------------")
            time.sleep(len(self.nodes)//10)  #
            iter_count = 0
            while not all([node.get_peer_count() == node_count-1 for node in self.nodes]):
                iter_count += 1
                print('waiting time: %f' % (0.5 * iter_count))
                if iter_count == 10:
                    for node in self.nodes[1:]:
                        node.add_peer(self.nodes[0].get_enode, 0)
                time.sleep(0.8)

    def get_parent_chain_id(self) -> str:
        """Return chain ID of parent chain."""
        if self.chain_id == '':
            print("Root chain has no parent chain.")
            return ''
        else:
            return self.chain_id[2:]

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
        time.sleep(0.05)
        threads = []
        for node in self.nodes:
            for other in other_chain.nodes:
                t = threading.Thread(target=other.add_peer, args=(node.get_enode(), 2))    # param 2 means upper peer
                t.start()
                time.sleep(0.1)    # if fail. add this line.
                threads.append(t)
                # time.sleep(0.3)

        for t in threads:
            t.join()
        time.sleep(0.5)

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
                time.sleep(0.1)
        for t in threads:
            t.join()
        time.sleep(1)

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


if __name__ == "__main__":
    ip_list = IPList(IP_CONFIG)
    ip_list.stop_all_containers()
    time.sleep(0.2)
    ip_list.remove_all_containers()
    node_count = 4
    c = SingleChain('01', 1, node_count, node_count*3//4+1, 121, ip_list)
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
    c.destruct_chain()
