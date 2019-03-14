#!/bin/bash
#ssh-keyscan $2 >> ~/.ssh/known_hosts
sshpass -p $4 scp docker/$1 $3@$2:$1
