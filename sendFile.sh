#!/bin/bash
sshpass -p 'Blockchain17' scp docker/$1 root@$2:$1
