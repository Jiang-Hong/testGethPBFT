#!/bin/bash
echo '*    soft    nproc    65530' >> /etc/security/limits.conf
echo '*    hard    nproc    65530' >> /etc/security/limits.conf
echo '*    soft    nofile    65530' >> /etc/security/limits.conf
echo '*    hard    nofile    65530' >> /etc/security/limits.conf
