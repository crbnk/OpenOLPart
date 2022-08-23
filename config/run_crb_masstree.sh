#!/bin/bash
NTHREADS=$2
QPS=$1
MAXREQS=1000
WARMUPREQS=200
TBENCH_QPS=${QPS} TBENCH_MAXREQS=${MAXREQS} TBENCH_WARMUPREQS=${WARMUPREQS} \
    TBENCH_MINSLEEPNS=100 /tmp/tailbench-v0.9/masstree/./mttest_integrated -j${NTHREADS} \
    mycsba masstree &

echo $! > integrated.pid

wait

python /tmp/tailbench-v0.9/utilities/parselats.py lats.bin > /tmp/share/masstree.txt
rm integrated.pid
