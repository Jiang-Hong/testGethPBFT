#!/bin/bash
echo '*    soft    noproc    65530' >> /etc/security/limits.conf
echo '*    hard    noproc    65530' >> /etc/security/limits.conf
echo '*    soft    nofile    65530' >> /etc/security/limits.conf
echo '*    hard    nofile    65530' >> /etc/security/limits.conf
