# coding: utf-8
# Author: crb
# Date: 2021/12/22 16:22
import sys
import os
import subprocess
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

app_docker_dict = {
    'masstree': "5069",
    'xapian': "3adb",
    'img-dnn': "306f",
    'sphinx': "f7eb",
    'moses': "ad58",
    'specjbb': "8900",
    'blackscholes': "881f",
    'canneal': "95d1",
    'fluidanimate': "b5ce",
    'freqmine': "cb3b",
    'streamcluster': "7bc0",
    'swaptions': "8b12"
}
tmp = ''
for k,v in app_docker_dict.items():
    tmp += f"docker restart {v} & "

# subprocess.run("sudo systemctl daemon-reload",shell=True)
# subprocess.run("sudo systemctl restart docker",shell=True)
subprocess.run(tmp,shell=True)