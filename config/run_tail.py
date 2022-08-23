import sys
import os
import subprocess
import datetime
import logging

bench_name = sys.argv[1]
QPS = sys.argv[2]
threads = sys.argv[3]


subprocess.call("cd /tmp/tailbench-v0.9/{} && /tmp/tailbench-v0.9/{}/./run_crb_{}.sh {} {}".format(bench_name,bench_name,bench_name,QPS,threads),shell=True)
    

