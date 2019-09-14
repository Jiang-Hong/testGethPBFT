#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.const import CONFIG, IP_CONFIG
from src.hibechain import HIBEChain
from src.iplist import IPList
from src.conf import load_config_file

import time

# TODO logging module
# TODO class decorators
# TODO finish benchmark function
# TODO reload module
# TODO wiki
# TODO docker push retry & make docker build faster

start_time = time.time()

ip_list = IPList(ip_file=IP_CONFIG)
ip_list.stop_all_containers()
time.sleep(1)
chain_id_list, thresh_list = load_config_file(config_file=CONFIG)
hibe = HIBEChain(chain_id_list=chain_id_list, thresh_list=thresh_list, ip_list=ip_list)
hibe.construct_hibe_chain()
hibe.set_number()
hibe.set_level()
hibe.set_id()

connect_time = time.time()
print("connect time %.3fs" % (connect_time-start_time))


root_chain = hibe.get_chain("")
r0 = root_chain.get_node_by_index(1)







# docker run -td rkdghd/geth-pbft:latest bash
# docker exec -t b82a7329d31e /usr/bin/geth --datadir abc account new --password passfile