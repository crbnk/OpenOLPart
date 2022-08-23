#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ../configs.sh

THREADS=$2
QPS=$1
MAXREQS=300
WARMUPREQS=50

BIN=./bin/moses_integrated

cp moses.ini.template moses.ini
sed -i -e "s#@DATA_ROOT#$DATA_ROOT#g" moses.ini

TBENCH_QPS=${QPS} TBENCH_MAXREQS=${MAXREQS} TBENCH_WARMUPREQS=${WARMUPREQS} \
    TBENCH_MINSLEEPNS=10000 ${BIN} -config ./moses.ini \
    -input-file ${DATA_ROOT}/moses/testTerms \
    -threads ${THREADS} -num-tasks 100000 -verbose 0 &

echo $! > integrated.pid
wait
python /tmp/tailbench-v0.9/utilities/parselats.py lats.bin > /tmp/share/moses.txt
rm integrated.pid
