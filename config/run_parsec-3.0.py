import sys
import os
import subprocess
import datetime
import logging


bench_name = sys.argv[1]
threads = sys.argv[2]

subprocess.call("cd /tmp/parsec-3.0 && /tmp/parsec-3.0/./run_crb.sh {} {}".format(bench_name,threads),shell=True)
