#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hibechain import HIBEChain
from iplist import IPList, exec_command
from conf import load_config_file
import time
import threading

#threading.stack_size(300*1024*1024)

#TODO function annotation
#TODO log  print lock
#TODO connection  peer reset -- set ClientAliveInterval ClientAliveCountMax TCPKeepAlive -- sshd_config all params
#TODO class decorators
#TODO paramiko connection reset by peer  broken pipe  ## about paramiko
#TODO PEP8 var name
#TODO connections  1. delay to all 2. remove some concurrencies
#TODO thread pool multiprocessing.pool
#TODO design limitation  shorten chain id

failCount = 0


def check_key_status(node):
    if node.key_status() is not True:
        print("keyStatus of node at %s:%s is False" % (node.ip, node.ethereum_network_port))
        print("node peer count is %s" % node.getPeerCount())
        global failCount
        failCount += 1


ip_list = IPList('ip.txt')
id_list, thresh_list = load_config_file('conf1.txt')

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
print("connect time %.3fs" % (connect_time-start_time))


a = hibe.get_chain("")
a1 = a.get_node_by_index(1)

#print('waiting for addPeer')
#count = 0
#while a1.getPeerCount() <= node_count-node_count//10:
#    print(a1.getPeerCount(), '.', end='')
#    count += 1
#    if count >= 20:
#        break
#    time.sleep(0.5)

print('another %s seconds waiting for addPeer' % str(10))
time.sleep(10)
print('peer count of a1----', a1.get_peer_count())

hibe.set_number()
hibe.set_level()
hibe.set_id()

end_time = time.time()

#print("level 0 keystatus", a1.key_status())
b = hibe.get_chain("0001")
b1 = b.get_node_by_index(1)
#print("level 1 keystatus", b1.key_status())
#c = hibe.getChain("0002")
#c1 = c.getNode(1)
#print("level 1 keystatus", c1.key_status())


threads = []
for chain in hibe.chains[1:]:
    for node in chain.nodes:
        t = threading.Thread(target=check_key_status, args=(node,))
        t.start()
        threads.append(t)
        time.sleep(0.1)
#        print(node.getPeerCount())
for t in threads:
    t.join()

desChainID = hibe.structed_chains[-1][0].chain_id
threads = []
for chain in hibe.structed_chains[-1]:
    print("chain id", chain.chain_id)
    tmpNode = chain.get_node_by_index(1)
    t = threading.Thread(target=tmpNode.test_send_transaction, args=(desChainID, 1, "0x1", 1, 250))
    time.sleep(1)
    t.start()
    threads.append(t)
    time.sleep(1)
for t in threads:
    t.join()


time.sleep(5)
consensus_chains = hibe.structed_chains[-2]
for chain in consensus_chains:
    p = chain.get_primer_node()
    p.txpool_status()

hibe.start_miner()

time.sleep(10)
count = 0
for chain in hibe.chains:
    for node in chain.nodes:
        print(node.get_peer_count(), end=" ")
        count += 1
    if count >= 20:
        break

transaction_chain_id = hibe.structed_chains[-1][0].chain_id[:-4]  # leaf chain
c = hibe.get_chain(transaction_chain_id)
p = c.get_primer_node()
for i in range(1, 10):
    p.get_block_transaction_count(i)


print("----------------------------------------------------------------")
print("node count", node_count)
print("connection time", connect_time - start_time)
print("total elapsed time:", end_time - start_time)
print("failCount", failCount)
print(time.ctime())
print("----------------------------------------------------------------")

c1 = hibe.get_chain('0001')
cr = hibe.get_chain('')
p1 = c1.nodes[0]
pr = cr.nodes[1]

tx_hash = p.get_transaction_by_block_number_and_index(1, 1)
tmp_chain = c
if tmp_chain:
    tmp_primer = tmp_chain.get_primer_node()
    while True:
        tmp_proof = tmp_primer.get_transaction_proof_by_hash(tx_hash)
        if tmp_proof:
            break
        else:
            time.sleep(0.01)

while True:
    tmp_chain = hibe.get_parent_chain(tmp_chain)
    if not hibe.is_root_chain(tmp_chain):
        tmp_primer = tmp_chain.get_primer_node()
        time.sleep(0.2)
        tmp_proof = tmp_primer.get_transaction_proof_by_proof(tmp_proof)
        if tmp_proof:
            continue
        else:
            while True:
                time.sleep(0.2)
                try:
                    tmp_proof = tmp_primer.get_transaction_proof_by_proof(tmp_proof)
                except Exception:
                    continue
                else:
                    break
            # if tmp_proof.get('error'):
            #     continue
            # elif tmp_proof:
            #     break
    else:
        break

tmp_primer = tmp_chain.get_primer_node()
time.sleep(0.2)
tmp_proof = tmp_primer.get_transaction_proof_by_proof(tmp_proof)
if not tmp_proof:
    while True:
        time.sleep(0.2)
        try:
            tmp_proof = tmp_primer.get_transaction_proof_by_proof(tmp_proof)
        except Exception:
            continue
        else:
            break

print(tmp_proof)





#hibe.destruct_hibe_chain()






# docker run -td rkdghd/geth-pbft:latest bash
# docker exec -t b82a7329d31e /usr/bin/geth --datadir abc account new --password passfile