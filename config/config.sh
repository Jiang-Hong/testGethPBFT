#!/bin/bash
while read -r line
do
  if [[ ! $line =~ [^[:space:]] ]] ; then
    break
  else
    echo $line
    echo test | sshpass -p test ssh -tt alice@$line sudo systemctl poweroff
    echo $?
  fi
done < ip.txt

## config requiretty
