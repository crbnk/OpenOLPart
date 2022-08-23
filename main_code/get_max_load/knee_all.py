import sys
import os
import subprocess
import datetime
import logging
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

bench_name =["specjbb","masstree","xapian","img-dnn","sphinx","moses"]
logging.basicConfig(filename="/tmp/share/knee_result.txt", level=logging.ERROR)
for name in bench_name:
    if name == "xapian":
        QPS = [i for i in range(0,6000,200)]
        WARMUPREQS = 8000
        REQUESTS = 4000
        for i in range(len(QPS)):
            now=datetime.datetime.now()
            logging.error("xapian {} {} {}".format(QPS[i],WARMUPREQS,REQUESTS))
            subprocess.call("cd /tmp/tailbench-v0.9/{} && /tmp/tailbench-v0.9/{}/./run.sh {} {} {}".format(name,name,QPS[i],WARMUPREQS,REQUESTS),shell=True)
            use_time = (datetime.datetime.now() - now).seconds
            logging.error("use_time,{}".format(use_time))

    if name == "masstree" or name == "img-dnn" or name == "specjbb":
        QPS = [10,20,30,40,50,60,70,80,90,100,200,300,400,500,600,700,800,900,1000,2000,3000,4000,5000,6000,7000,8000]
        REQUESTS = [1000,2000,4000,10000]
        for i in range(len(QPS)):
            for j in range(len(REQUESTS)):
                now=datetime.datetime.now()
                logging.error("{} {} {}".format(name,QPS[i],REQUESTS[j]))
                subprocess.call("cd /tmp/tailbench-v0.9/{} && /tmp/tailbench-v0.9/{}/./run.sh {} {}".format(name,name,QPS[i],REQUESTS[j]),shell=True)
                use_time = (datetime.datetime.now() - now).seconds
                logging.error("use_time,{}".format(use_time))

    if name == "sphinx":
        QPS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1, 2, 1.4, 1.6, 1.8, 2, 2.2, 2.4]
        REQUESTS = [1,2,5,10]
        #QPS=[0.1]
	    #REQUESTS=[1]
        for i in range(len(QPS)):
            for j in range(len(REQUESTS)):
                now = datetime.datetime.now()
                logging.error("sphinx qps{} req{} warmup {}".format(QPS[i], REQUESTS[j], max(REQUESTS[j]/2,1)))
                subprocess.call("cd /tmp/tailbench-v0.9/{} && /tmp/tailbench-v0.9/{}/./run.sh {} {} {}".format(name,name, QPS[i], REQUESTS[j], max(REQUESTS[j]//2,1)),
                                shell=True)
                use_time = (datetime.datetime.now() - now).seconds
                logging.error("use_time,{}".format(use_time))

    if name == "moses":
        QPS = [10,20,30,40,50,60,70,80,90,100,200,300,400,500]
        REQUESTS = [50,100,300,500,1000]
        for i in range(len(QPS)):
            for j in range(len(REQUESTS)):
                now = datetime.datetime.now()
                logging.error("moses {} {}".format(QPS[i], REQUESTS[j]))
                if REQUESTS[j]<300:
                    warm =10
                else:
                    warm=100
                subprocess.call(
                    "cd /tmp/tailbench-v0.9/{} && /tmp/tailbench-v0.9/{}/./run.sh {} {} {}".format(name,name, QPS[i], REQUESTS[j], warm),
                    shell=True)
                use_time = (datetime.datetime.now() - now).seconds
                logging.error("use_time,{}".format(use_time))
