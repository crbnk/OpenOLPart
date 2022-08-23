#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${DIR}/../configs.sh

THREADS=$2
REQS=100000000 # Set this very high; the harness controls maxreqs
TBENCH_QPS=$1
TBENCH_MAXREQS=1000
TBENCH_WARMUPREQS=500 TBENCH_MAXREQS=${TBENCH_MAXREQS} TBENCH_QPS=${TBENCH_QPS} \
    TBENCH_MINSLEEPNS=10000 TBENCH_MNIST_DIR=${DATA_ROOT}/img-dnn/mnist \
    /tmp/tailbench-v0.9/img-dnn/./img-dnn_integrated -r ${THREADS} \
    -f ${DATA_ROOT}/img-dnn/models/model.xml -n ${REQS} &
echo $! > integrated.pid

wait
python /tmp/tailbench-v0.9/utilities/parselats.py lats.bin > /tmp/share/img-dnn.txt

rm integrated.pid
