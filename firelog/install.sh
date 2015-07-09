#!/bin/bash
#title           :setup.sh
#description     :Installation and configuration script for the mPlane headless QoE probe.
#author          :marco.milanesio@eurecom.fr
#date            :20140716
#version         :0.1    
#usage           :bash setup.sh [--flume]
#bash_version    :4.2.45(1)-release
#==========================================================================================
flumeflag=1
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  echo "Usage: `basename $0` [--flume]"
  exit 0
fi
if [ -n "$1" ]; then
    if [ "$1" == "--flume" ]; then
        flumeflag=0
        echo "Flag set for flume agent."
    fi
fi


echo "Installing mPlane Firelog probe..."

echo "Installing additional software... Tstat"

TSTAT="eur-tstat-2.4.tar.gz"
wget "http://firelog.eurecom.fr/mplane/software/$TSTAT"
tar -xzf $TSTAT > /dev/null 
echo -n "Building ..."
TSTATDIR=$(pwd)/eur-tstat-2.4
cd $TSTATDIR
./autogen.sh 
./configure 
make
cd ..
echo "Done."

PHANTOM="phantomjs-1.9.7-linux-x86_64.tar.bz2"
echo -n "Installing additional software... phantomJS headless browser..."
wget "http://firelog.eurecom.fr/mplane/software/$PHANTOM"
tar xvf $PHANTOM
PHANTOMDIR=$(pwd)/phantomjs-1.9.7-linux-x86_64
echo "Done."

FLUME="apache-flume-1.5.2-bin.tar.gz"
if [ $flumeflag -eq 0 ]; then
    echo -n "Installing additional software... Apache Flume agent..."
    wget http://firelog.eurecom.fr/mplane/software/$FLUME
    tar xvf $FLUME > /dev/null
    echo "Done."
fi
FLUMEDIR=$(pwd)/apache-flume-1.5.2-bin

echo "Checking python3 ... "
if ! python3 -c 'import sys'
then
    echo "Python3 not found. Aborting ..."
    exit 1
fi
echo -n "Checking python3 modules ... "
if ! python3 -c 'import sqlite3'
then
    echo 'python module [ sqlite3 ] missing. Aborting.'
    exit 1
fi
if ! python3 -c 'import numpy'
then
    echo 'python module [ numpy ] missing. Aborting.'
    exit 1
fi
if ! python3 -c 'import json'
then
    echo 'python module [ json ] missing. Aborting.'
    exit 1
fi
if ! python3 -c 'import csv'
then
    echo 'python module [ csv ] missing. Aborting.'
    exit 1
fi
if ! python3 -c 'import urllib'
then
    echo 'python module [ urllib ] missing. Aborting.'
    exit 1
fi

echo "Done."

echo "Configuring Tstat ... "
list=$(ifconfig | egrep -i "wlan.|eth.|tun." | awk '{printf "%s ", $1 }')
set -- $list
echo -n "Select a network interface [ $list]:"
while read INTERFACE; do
    echo -n "Select a network interface [ $list]:"
    for i in $list; do
        if [ "$INTERFACE" == "$i" ]; then
            echo "Chosen $INTERFACE"
            found=0
            break
        else
            found=1
        fi
    done
    if [ $found -eq 0 ]; then
        break
    fi
done

IP=$(ifconfig $INTERFACE | grep "inet addr" | cut -d: -f2 | awk '{print $1}')
NETMASK=$(ifconfig $INTERFACE | grep "inet addr" | cut -d: -f4)
f=$(echo $IP | cut -d"." -f1,2,3 | awk '{print $0 ".0"}')
echo $TSTATDIR/tstat-conf/firelog-tstat.conf
echo $f/$NETMASK > $TSTATDIR/tstat-conf/firelog-tstat.conf
echo "Done."

echo "Configuring ..."
PROBEDIR=$(pwd)/phantomprobe
cd $PROBEDIR
sudo gcc -o script/start.out script/start.c
sudo gcc -o script/stop.out script/stop.c
sudo chmod 4755 script/*.out
cd ..
echo "Done."

echo -n "Enter your username:"
read USERNAME

echo "Writing configuration file"

echo "Done"

cat > $PROBEDIR/conf/firelog.conf <<EOL
[base]
dir=.
probedir=$PROBEDIR
backupdir=$PROBEDIR/session_bkp

[phantomjs]
dir=$PHANTOMDIR
profile=none
script=$PROBEDIR/script/netsniff_SB_v1.6.js
urlfile=$PROBEDIR/conf/url.list
thread_timeout=180
thread_outfile=/tmp/pjs_out.file
thread_errfile=/tmp/pjs_err.file
logfile=/tmp/pjs.log

[tstat]
dir=$TSTATDIR
netfile=$TSTATDIR/tstat-conf/firelog-tstat.conf
netinterface=$INTERFACE
logfile=/tmp/tstat.log
start=$PROBEDIR/script/start.out
stop=$PROBEDIR/script/stop.out
tstatout=/tmp

[database]
username=$USERNAME
dbfile=$PROBEDIR/probe.db
tstatfile=/tmp/tstat.out/log_own_complete
harfile=/tmp/phantomjs.har
table_raw=rawtable
table_active=active
table_aggr_sum=aggregate_summary
table_aggr_det=aggregate_details
table_probe=probe_id
table_diag_values=local_diag
table_diag_result=local_diag_result

[flume]
agentname=test
flumedir=$FLUMEDIR
confdir=$FLUMEDIR/conf
conffile=$PROBEDIR/conf/flume.conf
outdir=$PROBEDIR/.toflume
outfile=$PROBEDIR/.toflume/data.json
outfilecsv=$PROBEDIR/.toflume/data.csv

[server]
ip=193.55.113.252
port=13373

EOL

echo "Done. Please check the conf/firelog.conf file before proceeding."

echo "Cleaning installation..."
rm $TSTAT
rm $PHANTOM
if [ $flumeflag -eq 0 ]; then 
    rm $FLUME
fi

exit 0

