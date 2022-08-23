#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/../configs.sh

THREADS=1
AUDIO_SAMPLES='audio_samples'
#1
TBENCH_QPS=$1 
#10
TBENCH_MAXREQS=$2
#warmup 10
TBENCH_WARMUPREQS=1

LD_LIBRARY_PATH=/tmp/tailbench-v0.9/sphinx/./sphinx-install/lib:${LD_LIBRARY_PATH} \
    TBENCH_QPS=${TBENCH_QPS} TBENCH_MAXREQS=${TBENCH_MAXREQS} TBENCH_WARMUPREQS=${TBENCH_WARMUPREQS} TBENCH_MINSLEEPNS=10000 \
    TBENCH_AN4_CORPUS=${DATA_ROOT}/sphinx TBENCH_AUDIO_SAMPLES=${AUDIO_SAMPLES} \
    /tmp/tailbench-v0.9/sphinx/./decoder_integrated -t $THREADS &

echo $! > integrated.pid

wait
python /tmp/tailbench-v0.9/utilities/parselats.py lats.bin > /tmp/share/sphinx.txt

rm integrated.pid
