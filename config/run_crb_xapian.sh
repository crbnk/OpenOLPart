#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/../configs.sh

NSERVERS=$2
QPS=$1
WARMUPREQS=2000
REQUESTS=4000

TBENCH_QPS=${QPS} TBENCH_MAXREQS=${REQUESTS} TBENCH_WARMUPREQS=${WARMUPREQS} TBENCH_RANDSEED=0 \
       TBENCH_MINSLEEPNS=100000 TBENCH_TERMS_FILE=${DATA_ROOT}/xapian/terms.in \
       ./xapian_integrated -n ${NSERVERS} -d ${DATA_ROOT}/xapian/wiki -r 1000000000 &

echo $! > integrated.pid

wait
python /tmp/tailbench-v0.9/utilities/parselats.py lats.bin > /tmp/share/xapian.txt

rm integrated.pid

