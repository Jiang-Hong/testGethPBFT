#!/bin/bash
#ssh-keyscan $2 >> ~/.ssh/known_hosts
sshpass -p 'dell@2017' scp docker/$1 dell@$2:$1
