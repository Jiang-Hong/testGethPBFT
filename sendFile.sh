#!/bin/bash
ssh-keyscan $2 >> ~/.ssh/known_hosts
sleep 0.5s
sshpass -p 'Blockchain17' scp docker/$1 root@$2:$1
