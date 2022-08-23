#!/bin/bash
source /tmp/parsec-3.0/env.sh

bench_name=$1
threads=$2

parsecmgmt -a run -p ${bench_name} -i native -n ${threads} &


